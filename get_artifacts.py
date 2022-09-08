#!/usr/bin/env python3

import sys
import os
import fnmatch
import hashlib
import tempfile
import time
import shutil
import requests
import pathlib

from datetime import datetime, timedelta
from zipfile import ZipFile

here = os.path.abspath(os.path.dirname(__file__))


################################################################################
# Helper Functions
################################################################################


def get_envar(name):
    """
    Given a name, return the corresponding environment variable. Exit if not
    defined, as using this function indicates the envar is required.

    Parameters:
    name (str): the name of the environment variable
    """
    value = os.environ.get(name)
    if not value:
        sys.exit("%s is required." % name)
    return value


def abort_if_fail(response, reason):
    """
    If PASS_ON_ERROR, don't exit. Otherwise exit with an error and print
    the reason.

    Parameters:
    response (requests.Response) : an unparsed response from requests
    reason                 (str) : a message to print to the user for fail.
    """
    message = "%s: %s: %s\n %s" % (
        reason,
        response.status_code,
        response.reason,
        response.json(),
    )

    if os.environ.get("PASS_ON_ERROR"):
        print("Error, but PASS_ON_ERROR is set, continuing: %s" % message)
    else:
        sys.exit(message)


def set_env(name, value):
    """
    Helper function to echo a key/value pair to the environement file

    Parameters:
    name (str)  : the name of the environment variable
    value (str) : the value to write to file
    """
    environment_file_path = os.environ.get("GITHUB_ENV")

    with open(environment_file_path, "a") as environment_file:
        environment_file.write("%s=%s" % (name, value))


def get_file_hash(filepath, algorithm="sha256"):
    """return an md5 hash of the file based on a criteria level. This
    is intended to give the file a reasonable version.

    Parameters
    ==========
    image_path: full path to the singularity image
    """
    try:
        hasher = getattr(hashlib, algorithm)()
    except AttributeError:
        sys.exit("%s is an invalid algorithm." % algorithm)

    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def get_creation_timestamp(filename):
    """
    Get creation timestamp for a file
    """
    filen = pathlib.Path(filename)
    assert filen.exists()
    return filen.stat().st_ctime


def get_size(filename):
    filen = pathlib.Path(filename)
    assert filen.exists()
    return filen.stat().st_size


################################################################################
# Global Variables (we can't use GITHUB_ prefix)
################################################################################

API_VERSION = "v3"
BASE = "https://api.github.com"

# Github repository to check
repository = (
    os.environ.get("INPUT_REPOSITORY") or os.environ.get("GITHUB_REPOSITORY")
) or "buildsi/splice-experiment-runs"


HEADERS = {
    "Authorization": "token %s" % get_envar("GITHUB_TOKEN"),
    "Accept": "application/vnd.github.%s+json;application/vnd.github.antiope-preview+json;application/vnd.github.shadow-cat-preview+json"
    % API_VERSION,
}

# used to calculate if something is too old to parse
today = datetime.now()


# URLs
REPO_URL = "%s/repos/%s" % (BASE, repository)


def get_artifacts(repository, runid=None):
    """
    Retrieve artifacts for a repository.
    """
    # Check if the branch already has a pull request open
    results = []
    page = 1

    ARTIFACTS_URL = "%s/actions/artifacts" % REPO_URL
    if runid:
        ARTIFACTS_URL = "%s/actions/runs/%s/artifacts" % (REPO_URL, runid)

    while True:
        params = {"per_page": 100, "page": page}
        response = requests.get(ARTIFACTS_URL, params=params, headers=HEADERS)
        print("Retrieving page %s for %s" % (page, ARTIFACTS_URL))
        while response.status_code == 403:
            print("API rate limit likely exceeded, sleeping for 10 minutes.")
            time.sleep(600)
            response = requests.get(ARTIFACTS_URL, params=params, headers=HEADERS)
        if response.status_code != 200:
            abort_if_fail(response, "Unable to retrieve artifacts")
        response = response.json()
        results += response['artifacts']
        count = len(response["artifacts"])
        if count == 0:
            break
        page += 1

    return results


def recursive_find(base, pattern="*"):
    for root, _, filenames in os.walk(base):
        for filename in fnmatch.filter(filenames, pattern):
            yield os.path.join(root, filename)


def stream_download(url, dest):
    """
    stream download to file
    """
    with requests.get(url, stream=True, headers=HEADERS) as r:
        r.raise_for_status()
        with open(dest, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
    if os.path.exists(dest):
        return dest


def download_artifacts(artifacts, output, artifact_name=None):
    """
    Extract artifacts to an output directory
    """
    if not os.path.exists(output):
        os.makedirs(output)

    # Make cache output and results output
    for path in [output]:
        if not os.path.exists(path):
            os.makedirs(path)

    for artifact in artifacts:
        if artifact["expired"]:
            print(
                "Artifact %s from %s is expired."
                % (artifact["name"], artifact["created_at"])
            )
            continue

        artifact_url = artifact["archive_download_url"]

        # Create a temporary directory
        tmp = tempfile.mkdtemp()
        archive_path = os.path.join(tmp, "archive.zip")
        extract_dir = os.path.join(tmp, "extracted")

        # Make the extraction directory
        if not os.path.exists(extract_dir):
            os.makedirs(extract_dir)

        # Don't download results artifacts
        if artifact_name and artifact_name != artifact["name"]:
            continue
        print(f"Downloading {artifact_url}")

        zip_file = stream_download(artifact_url, archive_path)
        if not zip_file:
            print("Unable to download artifact %s" % artifact["name"])
            shutil.rmtree(tmp)
            continue

        # Read zipfile
        zipfile = ZipFile(zip_file, mode="r")
        zipfile.extractall(extract_dir)
        save_to = output

        # Loop through files, add those that aren't present
        for filename in recursive_find(extract_dir):
            relpath = filename.replace(tmp, "").strip(os.sep)
            finalpath = os.path.join(save_to, relpath)

            # If the file doesn't have size, don't add
            size = get_size(filename)
            if size == 0:
                print("Result file %s has size 0, skipping." % relpath)
                continue

            # If it doesn't exist, add right away!
            if not os.path.exists(finalpath):
                print("Found new result file: %s" % relpath)
                save_artifact(filename, finalpath)

            # Otherwise compare by hash
            else:
                newhash = get_file_hash(filename)
                oldhash = get_file_hash(finalpath)

                # If they aren't equal, compare by date and add newer
                if oldhash != newhash:
                    existing_timestamp = get_creation_timestamp(finalpath)
                    contender_timestamp = get_creation_timestamp(filename)
                    if contender_timestamp > existing_timestamp:
                        print("Found a newer result for %s" % relpath)
                        save_artifact(filename, finalpath)

        # Cleanup the temporary directory
        shutil.rmtree(tmp)


def save_artifact(source, destination):
    """
    Save an artifact.
    """
    destdir = os.path.dirname(destination)
    if not os.path.exists(destdir):
        os.makedirs(destdir)
    if os.path.exists(destination):
        os.remove(destination)
    shutil.copyfile(source, destination)


def main(runid=None):
    """
    main primarily parses environment variables to prepare for creation
    """
    output = os.environ.get("INPUT_OUTPUT", here)
    artifact_name = os.environ.get("INPUT_NAME")

    # Retrieve artifacts
    artifacts = get_artifacts(repository, runid)

    # Download artifacts to output directory
    download_artifacts(artifacts, output, artifact_name)


if __name__ == "__main__":
    runid = None
    if len(sys.argv) > 1:
        runid = sys.argv[1]
        print("Using runid %s" % runid)
    main(runid)

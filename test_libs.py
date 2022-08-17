# Find any .so libraries in a dest and move to a source.

import os
import sys
import fnmatch
import shutil
import json

import spliced.experiment.manual
import spliced.utils as utils
from spliced.logger import logger


def recursive_find(base):
    for root, _, filenames in os.walk(base):
        for filename in filenames:
            yield os.path.join(root, filename)


def get_prefix(lib):
    return os.path.basename(lib).split(".", 1)[0]


def main(first, second, os_a, os_b, outdir):

    # Create a lookup of prefixes for second libs
    prefixes = {}
    found = list(recursive_find(second))
    print("Found %s libs" % len(found))
    for lib in found:
        prefixes[get_prefix(lib)] = lib

    # Match first and second libs on .so
    # These should already be realpath from find_libs.py
    for lib in recursive_find(first):
        print("Looking for match to %s" % lib)
        lib = os.path.abspath(lib)
        lib_dir = os.path.dirname(lib).replace(first, "").strip("/")
        prefix = get_prefix(lib)
        print("Matching prefix %s" % prefix)
        if prefix in prefixes:
            second_lib = prefixes[prefix]
            print("Found match %s for %s" % (second_lib, lib))
        else:
            print("Did not find match for %s" % lib)
            continue

        experiment = "%s-%s-%s" % (prefix, os_a, os_b)
        outfile = os.path.join(outdir, "%s.json" % experiment)
        run_spliced(lib, second_lib, experiment, outfile)


def run_spliced(A, B, experiment_name, outfile):
    """
    Run a manual experiment
    """
    # A general SpackExperiment does a replacement
    experiment = spliced.experiment.manual.ManualExperiment()
    experiment.init(package=A, splice=B, experiment=experiment_name)

    # Perform the experiment
    experiment.run()
    experiment.predict(None, skip=["spack-test"], predict_type="diff")
    results = experiment.to_dict()
    utils.mkdir_p(os.path.dirname(os.path.abspath(outfile)))
    utils.write_json(results, outfile)
    print(json.dumps(results, indent=4))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("Expecting a first and second directory of libs as two arguments.")
    first = os.path.abspath(sys.argv[1])
    second = os.path.abspath(sys.argv[2])
    os_a = sys.argv[3]
    os_b = sys.argv[4]
    outdir = os.path.abspath(sys.argv[5])
    print(f"First directory {first}")
    print(f"Second directory {second}")
    print(f"OS A {os_a}")
    print(f"OS B {os_b}")
    print(f"Output directory {outdir}")
    os.listdir(first)
    os.listdir(second)
    main(first, second, os_a, os_b, outdir)

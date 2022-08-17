# Find any .so libraries in a dest and move to a source.

import os
import sys
import fnmatch
import shutil
import json

import spliced.experiment.manual
import spliced.utils as utils
from spliced.logger import logger


def recursive_find(base, pattern="*.so"):
    for root, _, filenames in os.walk(base):
        for filename in fnmatch.filter(filenames, pattern):
            yield os.path.join(root, filename)


def get_prefix(lib):
    return os.path.basename(lib).split(".", 1)[0]


def main(first, second, os_a, os_b, outdir):

    # Create a lookup of prefixes for second libs
    prefixes = {}
    found = list(recursive_find(second))
    for lib in found:
        prefixes[get_prefix(lib)] = lib

    # Match first and second libs on .so
    # These should already be realpath from find_libs.py
    for lib in recursive_find(first):
        lib = os.path.abspath(lib)
        lib_dir = os.path.dirname(first).replace(first, "").strip("/")
        prefix = get_prefix(lib)
        if prefix in prefixes:
            second_lib = prefixes[prefix]
        experiment = "%s-%s-%s" % (prefix, os_a, os_b)
        outfile = os.path.join(outdir, "%s.json" % experiment)
        run_spliced(lib, second_lib, experiment, outfile)


def run_spliced(A, B, experiment, outfile):
    """
    Run a manual experiment
    """
    # A general SpackExperiment does a replacement
    experiment = spliced.experiment.manual.ManualExperiment()
    experiment.init(package=A, splice=B, experiment=experiment)

    # Perform the experiment
    experiment.run()
    experiment.predict(args.predictor, skip=["spack-test"], predict_type="diff")
    results = experiment.to_dict()
    utils.mkdir_p(os.path.dirname(os.path.abspath(outfile)))
    utils.write_json(results, args.outfile)
    print(json.dumps(results, indent=4))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("Expecting a first and second directory of libs as two arguments.")
    first = os.path.abspath(sys.argv[1])
    second = os.path.abspath(sys.argv[2])
    os_a = os.path.abspath(sys.argv[3])
    os_b = os.path.abspath(sys.argv[4])
    outdir = os.path.abspath(sys.argv[5])
    main(first, second, os_a, os_b, outdir)
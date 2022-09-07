# Find any .so libraries in a dest and move to a source.

import argparse
import os
import sys
import fnmatch
import shutil
import json

import spliced.experiment.manual
import spliced.utils as utils
from spliced.logger import logger

# Test libs manual takes an input directory and subdirectory pattern
# to match, and then compares all pairs within it.


def recursive_find(base):
    for root, _, filenames in os.walk(base):
        for filename in filenames:
            yield os.path.join(root, filename)


def write_json(data, filename):
    with open(filename, "w") as fd:
        fd.write(json.dumps(data, indent=4))


def get_prefix(lib):
    """
    Create a prefix name for `lib`

    The prefix contains the directory name and all the characters
    in the file's name up to the first period.

    Ex:
       get_prefix("/usr/lib/libfoo.so") == "/usr/lib/libfoo"
       get_prefix("/usr/lib/libfoo.so.1.2") == "/usr/lib/libfoo"
    """
    dirname, filename = os.path.split(lib)
    prefix = filename.split(".", 1)[0]
    return os.path.join(dirname, prefix)


def run_analysis(first, second, os_a, os_b, outdir):
    """
    Main function to run the analysis between a first and second output
    directory. We have added start/stop indices for libraries because
    we cannot run them all in under 6 hours.
    """
    # Create a lookup of prefixes for second libs
    prefixes = {}
    found = [x for x in recursive_find(second) if ".so" in x and "lib" in x]
    print("Found %s libs" % len(found))

    # Prefixes are relative to 'second' directory
    #   If we have
    #     second='/usr' and lib='/usr/lib/libfoo.so.1'
    #   then
    #     prefixes = {'lib/libfoo':'/usr/lib/libfoo.so.1'}
    for lib in found:
        prefixes[os.path.relpath(get_prefix(lib), start=second)] = lib

    # Count in advance and sort so order is meaningful
    libs = [x for x in recursive_find(first) if ".so" in x and "lib" in x]
    libs.sort()

    print("Found %s sorted libs" % len(libs))

    # Match first and second libs on .so
    # These should already be realpath from find_libs.py
    for i, lib in enumerate(libs):
        # Only check within our range specified
        print("Looking for match to %s: %s of %s" % (lib, i, len(libs)))
        prefix = os.path.relpath(get_prefix(lib), start=first)
        print("Matching prefix %s" % prefix)
        if prefix in prefixes:
            second_lib = prefixes[prefix]
            print("Found match %s for %s" % (second_lib, lib))
        else:
            print("Did not find match for %s" % lib)
            continue

        experiment = "%s-%s-%s" % (prefix, os_a, os_b)
        outfile = os.path.join(outdir, "%s.json" % experiment)
        if not os.path.exists(outfile):
            lib = os.path.abspath(lib)
            second_lib = os.path.abspath(second_lib)
            print("%s vs. %s" % (lib, second_lib))
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
    #    experiment.predict(None, skip=["spack-test", "smeagle"], predict_type="diff")
    experiment.predict(names=["symbols"], predict_type="diff")
    results = experiment.to_dict()
    utils.mkdir_p(os.path.dirname(os.path.abspath(outfile)))
    utils.write_json(results, outfile)


def get_parser():
    parser = argparse.ArgumentParser(
        description="Fedora Test Runner",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    # Assume root is bound to data
    parser.add_argument(
        "root", help="root directory with subdirectories", default="/data"
    )
    parser.add_argument(
        "pattern", help="pattern of subdirectory to match (defaults to *)", default="*"
    )
    parser.add_argument("--outdir", help="output directory")
    return parser


def main():
    parser = get_parser()
    args, extra = parser.parse_known_args()

    # Show args to the user
    print("      root: %s" % args.root)
    print("     outdir: %s" % args.outdir)

    if not args.root or not os.listdir(args.root):
        sys.exit("A root directory with subdirectories for OS versions is required.")

    if not args.outdir:
        sys.exit("An output directory --outdir is required.")

    seen = set()
    for dirA in os.listdir(args.root):
        if not args.pattern in dirA:
            continue
        for dirB in os.listdir(args.root):
            if not args.pattern in dirB:
                continue
            uid = "-".join(sorted([dirA, dirB]))
            if uid in seen or dirA == dirB:
                continue
            seen.add(uid)
            print(uid)
            run_analysis(
                first=os.path.join(args.root, dirA),
                second=os.path.join(args.root, dirB),
                os_a=dirA,
                os_b=dirB,
                outdir=args.outdir,
            )


if __name__ == "__main__":
    main()

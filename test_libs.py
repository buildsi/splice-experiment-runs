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


def recursive_find(base):
    for root, _, filenames in os.walk(base):
        for filename in filenames:
            yield os.path.join(root, filename)


def get_prefix(lib):
    """
      Create a prefix name for `lib`
      
      The prefix contains the directory name and all the characters
      in the file's name up to the first period.
      
      Ex:
         get_prefix("/usr/lib/libfoo.so") == "/usr/lib/libfoo"
         get_prefix("/usr/lib/libfoo.so.1.2") == "/usr/lib/libfoo"
    """
    dirname,filename = os.path.split(lib)
    prefix = filename.split(".", 1)[0]
    return os.path.join(dirname,prefix)


def run_analysis(first, second, os_a, os_b, outdir, start=0, stop=5000):
    """
    Main function to run the analysis between a first and second output
    directory. We have added start/stop indices for libraries because
    we cannot run them all in under 6 hours.
    """
    # Create a lookup of prefixes for second libs
    prefixes = {}
    found = [x for x in recursive_find(second) if not os.path.relpath(x, start=second).startswith("usr/lib/debug")]
    print("Found %s libs" % len(found))

    # Prefixes are relative to 'second' directory
    #   If we have
    #     second='/usr' and lib='/usr/lib/libfoo.so.1'
    #   then
    #     prefixes = {'lib/libfoo':'/usr/lib/libfoo.so.1'}
    for lib in found:
        prefixes[os.path.relpath(get_prefix(lib), start=second)] = lib

    # Count in advance and sort so order is meaningful
    libs = [x for x in recursive_find(first) if not os.path.relpath(x, start=first).startswith("usr/lib/debug")]
    libs.sort()
    print("Found %s sorted libs" % len(libs))
    print("Start %s" % start)
    print("Stop %s" % stop)

    # Count libs separately
    count = 0

    # Match first and second libs on .so
    # These should already be realpath from find_libs.py
    for i, lib in enumerate(libs):
        # Only check within our range specified
        if count < start or count > stop:
            print("Skipping %s" % lib)
            continue
        count += 1
        print(
            "Looking for match to %s: %s of %s, count %s" % (lib, i, len(libs), count)
        )
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
    experiment.predict(None, skip=["spack-test", "smeagle"], predict_type="diff")
    results = experiment.to_dict()
    utils.mkdir_p(os.path.dirname(os.path.abspath(outfile)))
    utils.write_json(results, outfile)


def get_parser():
    parser = argparse.ArgumentParser(
        description="Fedora Test Runner",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument("first", help="first library directory to parse (positional)")
    parser.add_argument("second", help="second library directory to parse (positional)")
    parser.add_argument("--os_a", help="operating system tag for first")
    parser.add_argument("--os_b", help="operating system tag for second")
    parser.add_argument("--outdir", help="output directory")
    parser.add_argument("--start", help="start index in sorted libraries", default=0)
    parser.add_argument(
        "--stop", help="stopping index in sorted libraries", default=5000
    )

    return parser


def main():
    parser = get_parser()
    args, extra = parser.parse_known_args()

    # Show args to the user
    print("      first: %s" % args.first)
    print("     second: %s" % args.second)
    print("       os_a: %s" % args.os_a)
    print("       os_b: %s" % args.os_b)
    print("     outdir: %s" % args.outdir)
    print("      start: %s" % args.start)
    print("       stop: %s" % args.stop)

    if not args.first or not args.second:
        sys.exit(
            "A first and second directory of libs are required as positional arguments."
        )

    if not args.outdir:
        sys.exit("An output directory --outdir is required.")

    if not args.start:
        args.start = 0
    if not args.stop:
        args.stop = 5000

    run_analysis(
        first=args.first,
        second=args.second,
        os_a=args.os_a,
        os_b=args.os_b,
        outdir=args.outdir,
        start=int(args.start),
        stop=int(args.stop),
    )


if __name__ == "__main__":
    main()

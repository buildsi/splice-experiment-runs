# Find any .so libraries in a dest and move to a source.

import argparse
import os
import sys
import shutil
import tempfile
import subprocess

import spliced.experiment.manual
import spliced.utils as utils

from spliced.predict.base import time_run_decorator

debug_dirs = ["/usr/bin/.debug", "/usr/lib/debug"]


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
    dirname, filename = os.path.split(lib)
    prefix = filename.split(".", 1)[0]
    return os.path.join(dirname, prefix)


def run_analysis(first, second, os_a, os_b, outdir, start=0, stop=5000):
    """
    Main function to run the analysis between a first and second output
    directory. We have added start/stop indices for libraries because
    we cannot run them all in under 6 hours.
    """
    # Create a lookup of prefixes for second libs
    prefixes = {}
    found = [
        x
        for x in recursive_find(second)
        if not os.path.relpath(x, start=second).startswith("usr/lib/debug")
    ]
    print("Found %s libs" % len(found))

    # Prefixes are relative to 'second' directory
    #   If we have
    #     second='/usr' and lib='/usr/lib/libfoo.so.1'
    #   then
    #     prefixes = {'lib/libfoo':'/usr/lib/libfoo.so.1'}
    for lib in found:
        prefixes[os.path.relpath(get_prefix(lib), start=second)] = lib

    # Count in advance and sort so order is meaningful
    libs = [
        x
        for x in recursive_find(first)
        if not os.path.relpath(x, start=first).startswith("usr/lib/debug")
    ]
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
        if i < start or i > stop:
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
            lib = os.path.abspath(lib)
            second_lib = os.path.abspath(second_lib)
            print("%s vs. %s" % (lib, second_lib))
            run_spliced(lib, second_lib, experiment, outfile)

        # Assume we can now remove the libs to make space
        del prefixes[prefix]
        os.remove(lib)
        os.remove(second_lib)

        # This was second (largely unecessary) symbol analysis
        # outfile = os.path.join(outdir, "symbols_%s.json" % experiment)
        # if not os.path.exists(outfile):
        #    lib = os.path.abspath(lib)
        #    second_lib = os.path.abspath(second_lib)
        #    print("Symbols %s vs. %s" % (lib, second_lib))
        #    try:
        #        run_symbols_diff(lib, second_lib, first, second, experiment, outfile)
        #    except:
        #        print(f"Issue with {lib} and {second_lib}")


def get_debug_file(debug_info, path):
    """
    Given a loaded elf, parse the debuginfo path
    """
    if not debug_info:
        print("Elf does not have gnu_debuglink")
        return

    # Add extra debug directories - Fedora all ends with .debug
    if isinstance(debug_info, bytes):
        debug_info = (
            debug_info.decode("utf-8", errors="replace").split("debug")[0] + "debug"
        )
    debug_file = os.path.basename(debug_info)
    print(f"Looking for debug file {debug_file}")

    # Add the library specific search path
    debug_paths = debug_dirs.copy()
    debug_paths.append(path)

    # Look for debug info
    finds = []
    if not os.path.exists(debug_info):
        for root in debug_paths:
            finds += [x for x in recursive_find(root) if debug_file in x]
    print(finds)
    if not finds:
        print("No debug file found")
        return None
    return finds[0]


@time_run_decorator
def get_symbols(path):
    """
    Run nm to get symbols
    """
    out = tempfile.mktemp(suffix=".txt")
    res = os.system(
        'nm %s --format=posix --defined-only | awk \'{ if ($2 == "T" || $2 == "t" || $2 == "D") print $1 }\' | sort > %s'
        % (path, out)
    )
    if res != 0:
        return {}
    symbols = [x.strip() for x in utils.read_file(out).split("\n") if x.strip()]
    os.remove(out)
    print("Found %s symbols" % len(symbols))
    return {"symbols": symbols}


def run_symbols_diff(A, B, first, second, experiment_name, outfile):
    """
    The spliced symbols predictor cannot read debug direcly, so
    we try it here instead.

    first and second are the roots with debug info to find.
    """
    dest = tempfile.mkdtemp()
    with_debug_a = os.path.join(dest, os.path.basename(A))
    with_debug_b = os.path.join(dest, os.path.basename(B))

    # Generate new so with debug
    debugA = add_debug_info(A, with_debug_a, first)
    debugB = add_debug_info(B, with_debug_b, second)

    result = {
        "splice_type": "same_lib",
        "original_lib": A,
        "spliced_lib": B,
        "command": "missing-previously-found-symbols",
    }

    if not debugA or not debugB:
        print("One of A or B missing debug data.")
        result["message"] = "Missing debug data."
        return

    # Run nm for each
    before = get_symbols(debugA)
    after = get_symbols(debugB)
    missing_symbols = [x for x in before["symbols"] if x not in after["symbols"]]
    result["message"] = missing_symbols
    result["prediction"] = not missing_symbols
    result["time"] = before["seconds"] + after["seconds"]
    print(
        "Found %s missing symbols in %s seconds"
        % (len(missing_symbols), result["time"])
    )
    utils.mkdir_p(os.path.dirname(os.path.abspath(outfile)))
    utils.write_json(result, outfile)
    shutil.rmtree(dest)


def add_debug_info(lib, dest_lib, path):
    """
    Get lookup of debug file prefixes.
    """
    print("Looking for debuginfo file for %s" % lib)
    cmd = ["eu-readelf", "--string-dump=.gnu_debuglink", lib]
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = p.communicate()
    if p.returncode != 0:
        sys.exit(f"Issue asking for debug for {lib}")
    lines = [
        x for x in stdout.decode("utf-8", errors="ignore").split("\n") if x.strip()
    ]
    debug_link = lines[1]
    debug_link = debug_link.split(" ")[-1]

    # This finds the debug file in the path somewhere
    debug_file = get_debug_file(debug_link, path)
    print("Looking for name %s" % debug_file)
    if not debug_file:
        print("Cannot find debug file in %s" % debug_file)
        return

    cmd = ["eu-unstrip", lib, debug_file, "-o", dest_lib]
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = p.communicate()
    if p.returncode != 0:
        print(f"Issue adding debug info back {stderr}")
        return
    return dest_lib


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

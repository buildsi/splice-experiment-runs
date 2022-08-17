# Find any .so libraries in a dest and move to a source.

import os
import sys
import fnmatch
import shutil
import subprocess

debug_prefix = "/usr/lib/debug"


def recursive_find(base, pattern="*.so*"):
    for root, _, filenames in os.walk(base):
        for filename in fnmatch.filter(filenames, pattern):
            yield os.path.join(root, filename)


def add_debug_info(lib, dest_lib):
    """
    Get lookup of debug file prefixes.
    """
    print("Looking for debuginfo file for %s" % lib)
    cmd = ["eu-readelf", "--string-dump=.gnu_debuglink", lib]
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = p.communicate()
    if p.return_code != 0:
        sys.exit(f"Issue asking for debug for {lib}")
    lines = [
        x for x in stdout.decode("utf-8", errors="ignore").split("\n") if x.strip()
    ]
    debug_file = lines[1]
    debug_file = debug_file.split(" ")[-1]
    print("Found debug file name %s" % debug_file)
    if "debug" not in debug_file:
        print("Cannot find debug file in %s" % debug_file)
        return
    debug_path = "/usr/lib/debug" + os.path.dirname(lib) + "/" + debug_file
    if not os.path.exists(debug_path):
        sys.exit("Debug file %s does not exist" % debug_path)
    # Add debug info back
    cmd = ["eu-unstrip", lib, debug_path, "-o", dest_lib]
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
    if p.return_code != 0:
        print(f"Issue adding debug info back {stderr}")
        return
    return dest_lib


def main(src, dest):
    # Find so libs, along with debug
    for lib in recursive_find(src, "*.so*"):

        lib = os.path.realpath(lib)
        lib_dir = os.path.dirname(src).replace(src, "").strip("/")
        dest_lib = os.path.join(dest, lib_dir, os.path.basename(lib))
        if os.path.exists(dest_lib):
            continue
        # Either we write result to new location with debug
        add_debug_info(lib, dest_lib)

        # or copy the original
        if not os.path.exists(dest_lib):
            print("Copying %s to %s" % (lib, dest_lib))
            shutil.copyfile(lib, dest_lib)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("Expecting a src and dest as two arguments.")
    src = os.path.abspath(sys.argv[1])
    dest = os.path.abspath(sys.argv[2])
    main(src, dest)

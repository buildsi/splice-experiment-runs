# Find any .so libraries in a dest and move to a source.

import os
import sys
import fnmatch
import shutil


def recursive_find(base, pattern="*.so"):
    for root, _, filenames in os.walk(base):
        for filename in fnmatch.filter(filenames, pattern):
            yield os.path.join(root, filename)


def main(src, dest):
    for lib in recursive_find(src, "*.so"):
        lib = os.path.realpath(lib)
        lib_dir = os.path.dirname(src).replace(src, "").strip("/")
        dest_lib = os.path.join(dest, lib_dir, os.path.basename(lib))
        if os.path.exists(dest_lib):
            continue
        print("Copying %s to %s" % (lib, dest_lib))
        shutil.copyfile(lib, dest_lib)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("Expecting a src and dest as two arguments.")
    src = os.path.abspath(sys.argv[1])
    dest = os.path.abspath(sys.argv[2])
    main(src, dest)

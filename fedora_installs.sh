#!/bin/bash

dest_dir=$1
if test "x$dest_dir" = "x"; then
   echo "Usage: $0 DIR"
   exit -1
fi

declare -a libs=("libadwaita-qt5" "aspell" "boost-log", "clucene-core" "libdap" "samba-libs" "djvulibre-libs"
  "dovecot" "exiv2-libs" "gdal-libs" "geos" "glibmm24" "mozilla-openh264" "hdf5" "libicu" "dyninst" "webkit2gtk3-jsc"
  "webkit2gtk3-jsc" "libjxl" "libkml" "libmusicbrainz5" "openexr-libs" "openh264" "mesa-libOSMesa" "proj"
  "qt5-qtwayland" "qt5-qtxmlpatterns" "SDL2_image" "libstdc++" "taglib" "libreoffice-ure" "vtk"
  "webrtc-audio-processing" "python3"
)

# failed could not find "libicu67" (removed)

# We need to use eu-readelf to get .gnu-debuglink
dnf install -y elfutils

# install debug info plugin
dnf install -y dnf-plugins-core

dnf install -y findutils tree
for lib in "${libs[@]}"; do
   printf "dnf debuginfo-install -y ${lib}\n"
   
   # Adds debug info to (same path) plus debug in /usr/lib/debug
   dnf debuginfo-install -y ${lib}
   dnf install -y ${lib}
   
   # Copy the library's .so files into $dest_dir
   files=$(rpm -ql $lib | grep -E ".*\.so")
   for f in $files; do
      cp -Lu --parents $f $dest_dir/
   done
done

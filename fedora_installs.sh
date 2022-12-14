#!/bin/bash

# declare -a libs=("libadwaita-qt5" "aspell" "boost-log", "clucene-core" "libdap" "samba-libs" "djvulibre-libs"
#  "dovecot" "exiv2-libs" "gdal-libs" "geos" "glibmm24" "mozilla-openh264" "hdf5" "libicu" "dyninst" "webkit2gtk3-jsc"
#  "webkit2gtk3-jsc" "libjxl" "libkml" "libmusicbrainz5" "openexr-libs" "openh264" "mesa-libOSMesa" "proj"
#  "qt5-qtwayland" "qt5-qtxmlpatterns" "SDL2_image" "libstdc++" "taglib" "libreoffice-ure" "vtk"
#  "webrtc-audio-processing" "python3"
# )
# Install fewer (hopefully smaller, in time limit)
declare -a libs=("libadwaita-qt5" "aspell" "boost-log", "clucene-core" "libdap" "samba-libs" "djvulibre-libs"
  "dovecot" "exiv2-libs" "gdal-libs" "geos" "glibmm24" "hdf5" "libicu" "dyninst" "webkit2gtk3-jsc"
  "libjxl" "libkml" "libmusicbrainz5" "openexr-libs" "openh264" "mesa-libOSMesa" "proj"
  "qt5-qtwayland" "qt5-qtxmlpatterns" "SDL2_image" "libstdc++" "taglib" "vtk"
  "webrtc-audio-processing" "python3"
)
# failed could not find "libicu67" (removed)

# We need to use eu-readelf to get .gnu-debuglink
dnf install -y elfutils

# install debug info plugin
dnf install -y dnf-plugins-core
for lib in "${libs[@]}"; do
   printf "dnf debuginfo-install -y ${lib}\n"
   
   # Adds debug info to (same path) plus debug in /usr/lib/debug
   dnf debuginfo-install -y ${lib}
   dnf install -y ${lib}
done

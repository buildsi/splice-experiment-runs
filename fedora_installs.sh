#!/bin/bash

declare -a libs=("libadwaita-qt5" "aspell" "boost-log", "clucene-core" "libdap" "samba-libs" "djvulibre-libs"
  "dovecot" "exiv2-libs" "gdal-libs" "geos" "glibmm24" "mozilla-openh264" "hdf5" "libicu" "dyninst" "webkit2gtk3-jsc"
  "webkit2gtk3-jsc" "libjxl" "libkml" "libmusicbrainz5" "openexr-libs" "openh264" "mesa-libOSMesa" "proj"
  "qt5-qtwayland" "qt5-qtxmlpatterns" "SDL2_image" "libstdc++" "taglib" "libreoffice-ure" "vtk"
  "webrtc-audio-processing"
)

# failed could not find "libicu67" (removed)

dnf install -y findutils
for lib in "${libs[@]}"; do
   printf "dnf install ${lib}\n"
   dnf install -y ${lib}
done

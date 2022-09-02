#!/bin/bash

set -eu -o pipefail

# Core deps for ubuntu base
apt-get update && apt-get install -y build-essential libssl-dev vtable-dumper 

wget --quiet https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O ~/miniconda.sh && \
/bin/bash ~/miniconda.sh -b -p /opt/conda

export PATH=/opt/conda/bin:$HOME/.local/bin:$PATH
python -m pip install --upgrade pip 

python -m pip install ipython
CMAKE_VERSION=3.20.4
curl -s -L https://github.com/Kitware/CMake/releases/download/v$CMAKE_VERSION/cmake-$CMAKE_VERSION-linux-x86_64.sh > cmake.sh
sh cmake.sh --prefix=/usr/local --skip-license
rm cmake.sh

# Python dependencies
python -m pip install wheel
python -m pip install git+https://github.com/eliben/pyelftools
python -m pip install git+https://github.com/vsoch/elfcall@main
python -m pip install git+https://github.com/buildsi/spliced@use/smeagle-py

# Install abi-laboratory tools
git clone https://github.com/lvc/abi-dumper && \
cd abi-dumper && \
make install prefix=/usr && \
cd ../ && \
rm -rf abi-dumper && \
git clone https://github.com/lvc/abi-compliance-checker && \
cd abi-compliance-checker && \
make install prefix=/usr && \
cd ../ && \
rm -rf ./abi-compliance-checker

# Ensure spliced and other binaries available
which abicompat
which abidiff
which abi-dumper
which abi-compliance-checker
which spliced

# Ensure abi laboratory script added to path
printf "Copying ${SCRIPTS_DIR}/run_abi_laboratory.sh to ${INSTALL_BIN}/run_abi_laboratory.sh\n"
cp ${SCRIPTS_DIR}/run_abi_laboratory.sh ${INSTALL_BIN}/run_abi_laboratory.sh

#!/bin/bash

set -eu -o pipefail

# Ensure we can see Python installs
export PATH=/opt/conda/bin:$HOME/.local/bin:$PATH

lib=$1
A=first/$lib
B=second/$lib

# Check if exists in first and second
if [ ! -e "${A}" ]; then
    printf "First library ${A} does not exist."
fi
if [ ! -e "${B}" ]; then
    printf "Second library ${B} does not exist."
fi

results_dir=/tmp/results
cache_dir=/tmp/cache
mkdir -p ${results_dir} ${cache_dir}

export SPLICED_SMEAGLE_CACHE_DIR=${cache_dir}
export SPLICED_ABILAB_CACHE_DIR=${cache_dir}

printf "Results: ${results_dir}\n"
printf "Cache: ${cache_dir}\n"

export PATH=/usr/local/bin:${HOME}/.local/bin:/usr/bin:$PATH
ls


printf "Comparing ${A} vs ${B}\n"
outdir="${results_dir}/fedora/${lib}"
mkdir -p ${outdir}
experiment="fedora-${lib}"
outfile="${outdir}/experiment.json"
cmd="spliced diff --package ${A} --splice ${B} --experiment ${experiment} --runner manual --outfile ${outfile} --skip spack-test" 
printf "${cmd}\n"
${cmd}

if [ "$?" != "0" ]; then
    printf "Issue running command.\n"
    exit 1
fi
cat ${outfile}

#!/bin/bash

set -eu -o pipefail

# This script will be called by the abi-laboratory runner.

old=$1
new=$2
name=${3:-NAME}
report_path="${4}"
cleanup=false

printf "old: $old\n"
printf "new: $new\n"
printf "report: $report_path\n"

dira=$(dirname ${old})
dirb=$(dirname ${new})
export LD_LIBRARY_PATH="${dira}:${dirb}"

# cleanup if no custom report path is provided
if [ -z "${report_path+xxx}" ]; then 
    report_path=$(mktemp /tmp/report-XXXXX.html);
    printf "No report path provided, setting to $report_path\n"
    cleanup=true
fi
if [ -z "${old+xxx}" ]; then echo "Missing first argument, old library"; exit 1; fi
if [ -z "${new+xxx}" ]; then echo "Missing second argument, new library"; exit 1; fi

dump_old=$(mktemp /tmp/ABI-1-XXXXX.dump)
dump_new=$(mktemp /tmp/ABI-2-XXXXX.dump)

# Do we have custom debug directories?
DEBUG1=""
DEBUG2=""
if [ ! -z "$ABILAB_DEBUGINFO_DIR1" ]; then DEBUG1="--search-debuginfo=$ABILAB_DEBUGINFO_DIR1"; fi
if [ ! -z "$ABILAB_DEBUGINFO_DIR2" ]; then DEBUG2="--search-debuginfo=$ABILAB_DEBUGINFO_DIR2"; fi


# Options: https://github.com/lvc/abi-dumper/blob/master/abi-dumper.pl#L112
cd $dira
abi-dumper $old -o $dump_old -lver 1 $DEBUG1
cd -

cd $dirb
abi-dumper $new -o $dump_new -lver 2 $DEBUG2
cd -

# Options: https://github.com/lvc/abi-compliance-checker/blob/master/abi-compliance-checker.pl#L119
abi-compliance-checker -l $name -old $dump_old -new $dump_new -report-path $report_path
rm $dump_old
rm $dump_new

if [[ "${cleanup}" == "true" ]]; then
    rm $report_path
fi

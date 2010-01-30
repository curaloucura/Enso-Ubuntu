#! /bin/bash
script_dir="$(dirname "$(readlink -f ${BASH_SOURCE[0]})")"
echo $script_dir
export PYTHONPATH=$PYTHONPATH:$script_dir
$script_dir/scripts/run_enso.py

#TODO: don't run if another instance is running


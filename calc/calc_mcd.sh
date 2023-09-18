#!/usr/bin/env bash

work_path=/home/work_nfs5_ssd/hzli/kkcode/calc
cd ${work_path}

predict_acoustic_dir=$1
target_acoustic_dir=$2

python -u calc_mcd.py \
    --predict_acoustic_dir=${predict_acoustic_dir} \
    --target_acoustic_dir=${target_acoustic_dir}
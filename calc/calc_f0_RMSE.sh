#!/usr/bin/env bash

work_path=/home/work_nfs5_ssd/hzli/kkcode/calc
cd ${work_path}

predict_acoustic_dir=/home/disk1/hzli/syn/syn_2w/gl
target_acoustic_dir=/home/disk1/hzli/opencpop/22k_wavs

python -u calc_RMSE.py \
    ${predict_acoustic_dir} \
    ${target_acoustic_dir}
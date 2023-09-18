#!/bin/bash
old_wavs_dir=$1
norm_wavs_dir=${1}_norm
stage=0
set -euo pipefail

[ ! -e $norm_wavs_dir ] && mkdir -p $norm_wavs_dir

# norm wave -6db
if [ $stage -le 0 ];then
  echo "stage0: ####   norm wave -6 db   #####"
  startTime=`date +%Y%m%d-%H:%M`
  startTime_s=`date +%s`

  THREAD=20
  TMPFIFO=$$.fifo
  mkfifo $TMPFIFO
  exec 4<>${TMPFIFO}
  rm -rf ${TMPFIFO}

  {
  for((i=1; i<= $THREAD; i++))
  do
    echo;

  done
  } >&4

  for x in $old_wavs_dir/*.wav ;
  do
    read -u4

  {
    b=${x##*/}
    sox --norm=-6 $old_wavs_dir/$b  $norm_wavs_dir/tmp_$b
    mv $norm_wavs_dir/tmp_$b $norm_wavs_dir/$b
    echo "" >&4
  } &
  done <&4
  wait
  exec 4>&-
 
  endTime=`date +%Y%m%d-%H:%M`
  endTime_s=`date +%s`
  sumTime=$[ $endTime_s - $startTime_s ]
  useTime=$[ $sumTime ]
  echo "$startTime ---> $endTime" "Totl:$useTime seconds"
fi


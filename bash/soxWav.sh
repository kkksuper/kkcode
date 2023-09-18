#!/bin/bash
for x in ./*.wav
do 
  b=${x##*/}
  sox $b -r 22050 -c 1 -b 16 tmp_$b
  rm -rf $b
  mv tmp_$b $b
done
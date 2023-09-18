#!/bin/sh


count=$(ps -ef | grep -c kk_test)
if [ $count -lt 2 ]
then
    # 改动项 查询第1块gpu的容量--2p 第2块3p--2  第三块--4p  第四块--5p 
    stat2=$(gpustat | awk '{print $11}' | sed -n '5p')
    if [ "$stat2" -lt 1000 ]
    then
        echo 'run'
        #改动项 前面输入占用的gpu id 后面是运行代码
        CUDA_VISIBLE_DEVICES=3 python example.py
    fi
fi



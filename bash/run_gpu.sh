var=0
# work_path=/home/work_nfs5_ssd/hzli/acoustic_model/nice-fs2/egs/hw_chat-db6emo
work_path=$1

if [ "$#" != "1" ]; then
    echo "Usage: $0 bash dir"
    exit 1
fi
while [ $var -eq 0 ]
do
    count=0
    for i in $(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits)
    do
        # echo $count
        if [ $i -lt 10 ]
        then
            echo 'GPU'$count' is avaiable'
            # commod
            export CUDA_VISIBLE_DEVICES=$count  
            bash ${work_path}
            var=1
            exit 0
        fi
        count=$(($count+1))
    done
    echo $(date +%F%n%T)': no GPU is avaliable, wait for '$work_path
    sleep 5s  
done
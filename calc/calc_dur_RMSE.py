import os
import sys
import numpy as np

# 在 VISINGER2 解码时，将预测和真实的每个音素持续的帧数存为 numpy 数组，作为该脚本输入

num_dur = 0
dur_rmse = 0

record_dur_dir = sys.argv[1]
predict_dur_dir = sys.argv[2]

for file_name in os.listdir(record_dur_dir):
    record_dur = np.load(os.path.join(record_dur_dir, file_name)).reshape(-1)
    predict_dur = np.load(os.path.join(predict_dur_dir, file_name)).reshape(-1)
    
    dur_rmse += np.sum((record_dur - predict_dur) * (record_dur - predict_dur))
    num_dur += record_dur.shape[0]

print(np.sqrt(dur_rmse / num_dur))

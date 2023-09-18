import numpy as np
import matplotlib.pyplot as plt
import sys
import os
import sys
import numpy as np
import soundfile as sf
import pyworld as pw
import os
from tqdm import tqdm
from scipy.io import wavfile

sr = 44100
hop_size = 512
win_size = 2048

predict_dir = sys.argv[1]
target_dir = sys.argv[2]

rmse = []
corr = []

file_list = os.listdir(predict_dir)

for i in tqdm(range(len(file_list))):
    file_name = file_list[i]
    predict_path = os.path.join(predict_dir, file_name)
    target_path = os.path.join(target_dir, file_name)
    
    
    file_sr, predict_wav = wavfile.read(predict_path)
    file_sr, target_wav = wavfile.read(target_path)
    
    
    # 提取基频，由于这里输入了 sr，因此不需要预先对输入音频进行降采样操作
    predict_f0 , _ = pw.harvest(predict_wav.astype(np.float64), sr,
               frame_period=hop_size/sr*1000)
    
    target_f0 , _ = pw.harvest(target_wav.astype(np.float64), sr,
               frame_period=hop_size/sr*1000)

    # print(file_list[i])
    # print("len:{},{}".format(predict_f0.shape[0], target_f0.shape[0]))
    
    # align
    min_len = min(predict_f0.shape[0], target_f0.shape[0])
    print(predict_f0.shape[0], target_f0.shape[0])
    predict_f0 = predict_f0[:min_len]
    target_f0 = target_f0[:min_len]
    corr.append(np.corrcoef(predict_f0, target_f0))
    
    for j in range(min_len):
        if(predict_f0[j] != 0 and target_f0[j] != 0):
            # f0
            rmse.append((predict_f0[j] - target_f0[j]) * (predict_f0[j] - target_f0[j]))
            # lf0
            # rmse.append((math.log(predict_f0[j]) - math.log(target_f0[j])) * (math.log(predict_f0[j]) - math.log(target_f0[j])))

# print(min(rmse), max(rmse))
print("RMSE: ", np.sqrt(np.mean(np.array(rmse))))
print("F0 CORR: ", np.mean(np.array(corr)))

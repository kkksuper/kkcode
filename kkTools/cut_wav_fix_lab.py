import os
import soundfile as sf
from tqdm import tqdm
import traceback
from . import labelTools

# label_in_path = '/home/work_nfs5_ssd/hzli/data/fuxi_opensource_2/labels_whole_songs_tmp'
# label_out_path = '/home/work_nfs5_ssd/hzli/data/fuxi_opensource_2/labels'

label_in_path = "/home/work_nfs5_ssd/hzli/kkcode/tmp1"
label_out_path = "/home/work_nfs5_ssd/hzli/data/jubei2021/no_trimmed_labels"
# label_out_path = "/home/work_nfs5_ssd/hzli/data/jubei2021/labels"

wav_in_path = '/home/work_nfs5_ssd/hzli/data/fuxi_opensource_2/acoustic_features_22k_hop256_win1024/wavs'
wav_out_path = '/home/work_nfs5_ssd/hzli/data/fuxi_opensource_2/wavs'

sample_rate = 22050
win_size = 1024
hop_size = 256
sil_frame = 50
sil_sample = sil_frame * hop_size
sil_time = sil_sample / sample_rate
cutTime = {}

is_cut_wav = True
is_cut_wav = False

is_cut_sil = True
is_cut_sil = False

limit_min_phone_num = True
phone_min_num = 10


def cutwav(wav_name, out_name, startTime, endTime):

    wav_name = os.path.join(wav_in_path, wav_name)
    out_name = os.path.join(wav_out_path, out_name)

    # print("cut " + wav_name + " from " + str(startTime) + " to " + str(endTime))

    inaudio, sr = sf.read(wav_name)
    start = int(startTime * sr)
    end = int(endTime * sr)
    sf.write(out_name, inaudio[start:end], sr)

    # print("wav saved in " + out_name)
    return


def cutLabelSil(filename):
    '''
    遍历每一个label_whole_song文件 \n
    将大于设定长度的静音时间减小到设定值 \n
    计算开始时间和结束时间，并传入cutwav方法中，完成音频切分 \n
    去掉xmin和xmax字段，写新label \n
    start_time 表示当前音频的起始点，如果某rest过长，则下一label的start_time等于(xmax - sil_time)，本label的end_time等于(xmin + sil_time)
    '''

    phone, pitch, slur, pho_pos_in_note, num, score_duration, real_duration, xmin, xmax = labelTools.label2list_has_minmax_in_attr(
        os.path.join(label_in_path, filename))

    out_name = os.path.join(label_out_path, filename.split('.')[0] + '_0.lab')
    out_label = open(out_name, "w")

    file_num = 0
    start_time = xmin[0]
    end_time = xmax[0]
    tmp_time = 0.0

    if real_duration[0] > sil_time and is_cut_sil:
        score_duration[0] = sil_time
        real_duration[0] = sil_time
        start_time = xmax[0] - sil_time

    phone_count = 0

    for index in range(len(phone)):

        if index > 0 and phone[index] == "rest":

            if real_duration[index] > sil_time and is_cut_sil:
                score_duration[index] = sil_time
                real_duration[index] = sil_time
                end_time = xmin[index] + sil_time
                tmp_time = xmax[index] - sil_time
            else:
                end_time = xmax[index]
                tmp_time = xmin[index]

        line = '\t'.join(
            (phone[index], pitch[index], slur[index],
             pho_pos_in_note[index], num[index], str(score_duration[index]),
             str(real_duration[index])))
        out_label.write(line + "\n")

        # 限制音素的最少数量
        phone_count += 1
        if limit_min_phone_num and phone_count < phone_min_num:
            continue

        if index > 0 and phone[index] == "rest":

            phone_count = 0

            # print("save in " + out_name)
            if is_cut_wav:
                cutwav(filename[0:-3] + "wav",
                       out_name.split('/')[-1][0:-3] + "wav", start_time,
                       end_time)

            if index != len(phone) - 1:
                start_time = tmp_time
                file_num += 1
                out_name = os.path.join(
                    label_out_path,
                    filename.split('.')[0] + '_{}.lab'.format(file_num))
                out_label = open(out_name, 'w')
                out_label.write(line + "\n")


def main():

    labels = [os.path.basename(path) for path in os.listdir(label_in_path)]
    labels.sort()
    debug = False
    # debug = True

    if (not os.path.isdir(label_out_path)):
        os.mkdir(label_out_path)

    if (not os.path.isdir(wav_out_path)):
        os.mkdir(wav_out_path)

    for filename in tqdm(labels):
        try:
            if filename.endswith(".lab"):
                if debug:
                    if filename == "2024.lab":
                        cutLabelSil(filename)
                else:
                    cutLabelSil(filename)
        except Exception as e:
            print("\nfailed deal with " +
                  os.path.join(label_in_path, filename))
            traceback.print_exc()
            break


if (__name__ == "__main__"):
    main()

import os
import soundfile as sf
import pyworld as pw
from tqdm import tqdm
import traceback
import glob
import functools
import numpy as np
from . import multiTask, scpTools, dirTools, tools
import librosa
import xlwt
from scipy.interpolate import interp1d


def load_wav(wav_path, target_sr=24000, padding=True, win_size=1024, hop_size=256):
    audio, raw_sr = librosa.core.load(wav_path, sr=None)
    if raw_sr != target_sr:
        audio = librosa.core.resample(
            audio, orig_sr=raw_sr, target_sr=target_sr, res_type="kaiser_best"
        )
        if padding:
            target_length = (audio.size // hop_size + win_size // hop_size) * hop_size
            pad_len = (target_length - audio.size) // 2
            if audio.size % 2 == 0:
                audio = np.pad(audio, (pad_len, pad_len), mode="reflect")
            else:
                audio = np.pad(audio, (pad_len, pad_len + 1), mode="reflect")
    return audio


def get_ttsing_sillist(label_dir, name):
    '''
    从每个label中得到其最后一行静音的时长
    '''
    labels = [
        os.path.basename(path) for path in glob.glob(label_dir + "/*.lab")
        if os.path.basename(path).startswith(name)
    ]
    labels.sort(key=functools.cmp_to_key(tools.sort_1))
    sil_list = []
    for label in labels:
        with open(os.path.join(label_dir, label)) as f:
            sil_list.append(f.readlines()[-1].split('\t')[5].strip())
    return sil_list


def concat_wav_by_start_cutsil(in_dir, out_dir, sil_list, name):
    '''
    切除之间的静音，拼接音频，sil_list为每个音频开头需要切掉的时间(s)
    '''
    os.makedirs(out_dir, exist_ok=True)

    wavs = [
        os.path.basename(path) for path in glob.glob(in_dir + "/*.wav")
        if os.path.basename(path).startswith(name)
    ]
    wavs.sort(key=functools.cmp_to_key(tools.sort_1))
    assert len(wavs) == len(
        sil_list
    ), "wavs len is differ from sil_list, wav: {}, sil list: {}".format(
        len(wavs), len(sil_list))

    outaudio, sr = sf.read(os.path.join(in_dir, wavs[0]))

    for index in range(len(wavs)):
        if index == 0:
            continue
        tmpaudio, sr = sf.read(os.path.join(in_dir, wavs[index]))
        begin = int(float(sil_list[index]) * sr)
        outaudio = np.hstack((outaudio, tmpaudio[begin:]))

    sf.write(os.path.join(out_dir, name + ".wav"), outaudio, sr)


def concat_wav_by_start(in_dir, out_dir, name):
    '''
    拼接文件夹下以名字以name开头的音频，并在out_dir路径下生成名为name的音频
    '''
    os.makedirs(out_dir, exist_ok=True)

    wavs = [
        os.path.basename(path) for path in glob.glob(in_dir + "/*.wav")
        if os.path.basename(path).startswith(name)
    ]

    assert len(wavs) != 0, "no satisfied wav"

    wavs.sort()
    # wavs.sort(key=functools.cmp_to_key(tools.sort_1))

    outaudio, sr = sf.read(os.path.join(in_dir, wavs[0]))

    for index in range(len(wavs)):
        if index == 0:
            continue
        tmpaudio, sr = sf.read(os.path.join(in_dir, wavs[index]))
        outaudio = np.hstack((outaudio, tmpaudio))

    sf.write(os.path.join(out_dir, name + ".wav"), outaudio, sr)


def concat_wav_by_scp(in_dir, out_dir, scp):
    '''
    拼接文件夹下文件名在scp中的音频 \n
    out_dir为文件的路径，不是文件夹的路径 \n
    scp 中的 name不需要后缀
    '''
    wavs = [os.path.join(in_dir, i + ".wav") for i in scp]
    # wavs = [os.path.join(in_dir, i+".wav") for i in name_list]

    outaudio, sr = sf.read(wavs[0])

    for index in range(len(wavs)):
        if index == 0:
            continue
        tmpaudio, sr = sf.read(wavs[index])
        outaudio = np.hstack((outaudio, tmpaudio))

    sf.write(out_dir, outaudio, sr)


def concat_wav_by_scp_with_sil(in_dir, out_dir, scp, sil_len=10000):
    '''
    拼接文件夹下文件名在scp中的音频 \n
    out_dir为文件的路径，不是文件夹的路径 \n
    scp 中的 name不需要后缀
    '''
    wavs = [os.path.join(in_dir, i + ".wav") for i in scp]
    # wavs = [os.path.join(in_dir, i+".wav") for i in name_list]
    sil = np.zeros(sil_len)

    outaudio, sr = sf.read(wavs[0])

    for index in range(len(wavs)):
        if index == 0:
            continue
        tmpaudio, sr = sf.read(wavs[index])
        outaudio = np.hstack((outaudio, sil, tmpaudio))

    sf.write(out_dir, outaudio, sr)


def downSample(utt, in_dir, out_dir, target_sr):
    '''
    将输入路径下的wav文件，降采样到目标采样率
    '''
    os.makedirs(out_dir, exist_ok=True)

    file_name = "{}.wav".format(utt)

    try:
        if not os.path.isfile(file_name):
            os.system("sox " + os.path.join(in_dir, file_name) + " -b 16 -r " +
                      target_sr + " --norm=-6 " +
                      os.path.join(out_dir, file_name))
    except Exception as e:
        print("error: ", file_name)
        traceback.print_exc()
        return "error in {}".format(utt)

    return


def downSample_scp(scp, args):
    '''
    将输入路径下的所有在scp中的wav文件，降采样到目标采样率, 输出目录一般要以 / 结尾
    '''
    in_dir, out_dir, target_sr = args[0], args[1], args[2]

    os.makedirs(out_dir, exist_ok=True)

    num = 0
    # print("deal with " + in_dir)
    file_names = glob.glob(in_dir + "/*.wav")
    file_names.sort()

    for index in tqdm(range(len(file_names))):
        file_name = os.path.split(file_names[index])[1]
        if not os.path.isfile(os.path.join(out_dir + file_name)
                              ) and os.path.splitext(file_name)[0] in scp:
            os.system("sox " + file_names[index] + " -b 16 -r " + target_sr +
                      " --norm=-6 " + out_dir + "/" + file_name)

    num += len(file_names)
    return num


def wav_to_one_channel(scp, args):
    '''
    将输入路径下的所有在scp中的wav文件，降为单通道, 输出目录一般要以 / 结尾
    '''
    in_dir, out_dir = args[0], args[1]

    os.makedirs(out_dir, exist_ok=True)

    num = 0
    # print("deal with " + in_dir)
    file_names = glob.glob(in_dir + "/*.wav")
    file_names.sort()

    for index in tqdm(range(len(file_names))):
        file_name = os.path.split(file_names[index])[1]
        if not os.path.isfile(os.path.join(out_dir + file_name)
                              ) and os.path.splitext(file_name)[0] in scp:
            os.system("sox " + file_names[index] + " -c 1 " + out_dir + "/" +
                      file_name)

    num += len(file_names)
    return num


def get_wav_sample(wav_path, sr=24000):
    audio = librosa.load(wav_path, sr=sr)[0]
    return audio.shape[0]


def get_wav_duration(wav_path):
    '''
    返回wav的时间(单位：秒)
    '''
    d = librosa.get_duration(filename=wav_path)
    return d


def get_wav_frame(wav_path, sr, hop_size):
    '''
    返回wav的帧长
    '''
    d = librosa.get_duration(filename=wav_path)
    return d * sr // hop_size


def get_wav_sr(wav_path):
    '''
    返回wav的采样率
    '''
    try:
        wav, sr = sf.read(wav_path)
        return sr
    except Exception as e:
        print("error: ", wav_path)
        traceback.print_exc()
        exit(0)


def get_wavs_duration(in_dir, utts):
    '''
    返回indir下, utts中wav的时间(单位：秒)
    '''
    utt2duration = {}
    for utt in tqdm(utts):
        wav_path = os.path.join(in_dir, utt + ".wav")
        utt2duration[utt] = get_wav_duration(wav_path)
    return utt2duration


def get_wavs_frame(in_dir, utts, sr, hop_size):
    '''
    返回indir下, utts中wav的帧长
    '''
    frames = []
    for utt in tqdm(utts):
        wav_path = os.path.join(in_dir, utt + ".wav")
        frames.append(get_wav_frame(wav_path, sr, hop_size))
    return frames


def get_wavs_sr(in_dir, utts):
    '''
    返回indir下, utts中wav的采样率
    '''
    srs = []
    for utt in tqdm(utts):
        wav_path = os.path.join(in_dir, utt + ".wav")
        srs.append(get_wav_sr(wav_path))
    return srs


def flac2wav(in_dir, out_dir):
    '''
    将 indir 下的所有flac文件转为wav, 并存到 outdir
    '''
    infiles = glob.glob(in_dir + "/*.flac")
    for f in infiles:
        name = os.path.splitext(os.path.basename(f))[0]
        if os.path.isfile(os.path.join(out_dir, name + ".wav")):
            continue
        sh = "ffmpeg -i " + f + " " + os.path.join(out_dir, name + ".wav")
        os.system(sh)


def find_wav_times(in_dir, utts=None, prefix="", seq='_'):
    '''
    搜集路径下所有 wav 文件，获取他们的时长，返回 dict
    '''
    utt2len = {}
    if utts is None:
        utts = glob.glob(in_dir + "/*.wav")
        utts = [os.path.splitext(os.path.basename(i))[0] for i in utts]
    for utt in tqdm(utts):
        try:
            utt2len[prefix + seq +
                    utt if prefix != "" else utt] = get_wav_duration(
                        os.path.join(in_dir, f"{utt}.wav"))
        except:
            traceback.print_exc()
            continue
    return utt2len


def find_wav_times_r(rootDir,
                     prefix="",
                     seq='_',
                     exclude_dirs=[],
                     exclude_files=[]):
    '''
    搜集路径下所有 wav 文件，获取他们的时长(递归)，返回 dict
    '''
    if not os.path.isdir(rootDir):
        print("this seem is not a dir: " + rootDir)
        return
    print("deal with dir:" + rootDir)
    files = os.listdir(rootDir)
    utt2len = {}
    for file in files:
        try:
            cur_path = os.path.join(rootDir, file)
            if os.path.isdir(cur_path):
                if file in exclude_dirs:
                    continue
                print("go to dir:" + cur_path)
                get_utt2len = find_wav_times_r(cur_path, prefix + file, seq,
                                               exclude_dirs, exclude_files)
                utt2len.update(get_utt2len)
            elif file.endswith(".wav"):
                if file[:-4] in exclude_files:
                    continue
                utt2len[prefix + seq +
                        os.path.splitext(file)[0]] = get_wav_duration(cur_path)
        except Exception as e:
            print("error file: " + file)
            traceback.print_exc()
            continue
    return utt2len


def export_wav_time_xlsx(in_dir,
                         outfile=None,
                         mode="",
                         prefix="",
                         seq="_",
                         exclude_dirs=[],
                         exclude_files=[]):
    '''
    mode:\n
    \tdefalut: only in indir
    \t-r: 递归查找
    '''
    if mode == "":
        utt2len = find_wav_times(in_dir, prefix, seq)
    elif mode == "-r":
        utt2len = find_wav_times_r(in_dir, prefix, seq, exclude_dirs,
                                   exclude_files)
    else:
        raise NotImplementedError

    # print(in_dir)
    workbook = xlwt.Workbook(encoding='utf-8')  #create excel file
    count_misc = 0.0
    
    utts = [utt for utt in utt2len]
    sheetlen = len(utt2len) // 60000 + 1
    for sheetindex in range(sheetlen):
        sheet = workbook.add_sheet(f'wav_data_{sheetindex}')
        line = 0
        for utt in utts[sheetindex*60000: (sheetindex+1)*60000]:
            sheet.write(line, 0, utt)
            sheet.write(line, 1, utt2len[utt])
            line += 1
            count_misc += float(utt2len[utt])
        

    if outfile is not None:
        workbook.save(outfile)

    print(f"{len(utt2len)} utts")
    print(str(count_misc / 60.0) + ' min')
    print(str(count_misc / 3600.0) + ' h')

def extract_pitch_use_dio(utt, wav_dir, sr=16000, hop_size=200, use_lf0=False):
    '''
    输入 wav 的路径以及采样率和帧移，返回 f0 或者 lf0 （use_lf0 可选）
    '''
    wav_path = os.path.join(wav_dir, f"{utt}.wav")
    wav, sr = librosa.load(wav_path, sr=sr)
    f0, _ = pw.dio(wav.astype(np.float64),
                    sr,
                    frame_period=hop_size / sr * 1000)
    
    if use_lf0:
        f0 = np.log(f0 + 1e-8)
        f0[f0 < 1e-3] = 0
        
    f0 = f0.astype(np.float32)
    return f0


def extract_pitch_use_harvest(utt, wav_dir, sr=16000, hop_size=200, use_lf0=False):
    '''
    输入 wav 的路径以及采样率和帧移，返回 f0 或者 lf0 （use_lf0 可选）
    '''
    wav_path = os.path.join(wav_dir, f"{utt}.wav")
    wav, sr = librosa.load(wav_path, sr=sr)
    f0,t = pw.harvest(wav.astype(np.float64), sr, frame_period=hop_size/sr*1000)
    f0 = pw.stonemask(wav.astype(np.float64),f0, t, sr)
    
    if use_lf0:
        f0 = np.log(f0 + 1e-8)
        f0[f0 < 1e-3] = 0
        
    f0 = f0.astype(np.float32)
    return f0
    
def extract_pitch_use_harvest_and_dio(utt, wav_dir, sr=16000, hop_size=200, use_lf0=False):
    '''
    输入 wav 的路径以及采样率和帧移，返回 f0 或者 lf0 （use_lf0 可选）
    '''
    wav_path = os.path.join(wav_dir, f"{utt}.wav")
    wav, sr = librosa.load(wav_path, sr=sr)
    f0_harvest, t = pw.harvest(wav.astype(np.float64), sr, frame_period=hop_size/sr*1000)
    f0_harvest = pw.stonemask(wav.astype(np.float64), f0_harvest, t, sr)
    f0_dio, _ = pw.dio(wav.astype(np.float64),
                    sr,
                    frame_period=hop_size / sr * 1000)
    uv = np.where(f0_harvest > 0, 1, 0)
    f0 = func_interp1d(f0_dio, uv)
    f0 = np.where(f0 > 0, np.log(f0), 0.)
    if use_lf0:
        f0 = np.log(f0 + 1e-8)
        f0[f0 < 1e-3] = 0
    return f0


def func_interp1d(f0, uv):
    nonzero_ids = np.where(f0 != 0)[0]
    if len(nonzero_ids) > 1:
        interp_fn = interp1d(nonzero_ids, f0[nonzero_ids], fill_value=(f0[nonzero_ids[0]], f0[nonzero_ids[-1]]), bounds_error=False)
        f0 = interp_fn(np.arange(0, len(f0)))
        f0[uv == 0] = 0
    return f0

def main():

    mode = 16

    if mode == 1:
        # label_in_path = '/home/work_nfs4_ssd/xueheyang/workspace/data/F001_labelled/train_phone_level_gt_labels/'
        label_in_path = "/home/work_nfs/ymzhang/ttsing_frontend/data/100-songs/features_12_5ms_50sil/unaligned_test_label_subpitch"
        in_dir = '/home/work_nfs4_ssd/hzli/logdir/100songs-delightful_conformer_gan_f0/refinegan/'
        out_dir = '/home/work_nfs4_ssd/hzli/logdir/100songs-delightful_conformer_gan_f0/refine_whole_cut/'
        # names = ["006", "012", "020", "021"]
        names = ["006"]
        for name in tqdm(names):
            sil_list = get_ttsing_sillist(label_in_path, name)
            concat_wav_by_start_cutsil(in_dir, out_dir, sil_list, name)
    elif mode == 2:
        dir1 = "/home/work_nfs5_ssd/hzli/data/niren/230210/acoustic_feature/wavs"
        dir2 = "/home/work_nfs5_ssd/hzli/data/niren/230210/acoustic_feature/wavs_16k"
        sr = "16000"
        multiTask.multiThread_use_multiprocessing_multiarg(
            scpTools.genscp_in_list(dir1), 20, downSample_scp, dir1, dir2, sr)
    elif mode == 3:
        in_dir = '/root/workspace/syn/syn_M_680/gl/'
        out_dir = '/root/workspace/syn/syn_M_680/whole_song/'
        names = ["2044", "2086", "2092", "2093", "2100"]
        for name in tqdm(names):
            concat_wav_by_start_cutsil(in_dir, out_dir, name)
    elif mode == 4:
        # big data 766.17 小时
        wav_dir = '/home/work_nfs5_ssd/hzli/data/big_data/wavs/'
        utts = scpTools.scp2list("/home/work_nfs5_ssd/hzli/data/big_data/file_lst/all.lst")
        # utts = scpTools.genscp_in_list(wav_dir)
        utt2dur = get_wavs_duration(wav_dir, utts)
        total = sum([utt2dur[i] for i in utt2dur])
        print(total)
    elif mode == 5:
        wav_in_path = "/home/work_nfs4_ssd/hzli/logdir/100songs-delightful_conformer_gan_f0/hifigan"
        wav_out_path = wav_in_path + "_wholeSong"
        for name in ["006", "012", "020", "021"]:
            concat_wav_by_start(wav_dir, wav_out_path, name)
    elif mode == 6:
        in_dir = "/home/work_nfs5_ssd/hzli/kkcode/tmp/tmp_wavs/gt/zero"
        out_dir = "/home/work_nfs5_ssd/hzli/kkcode/tmp/tmp_wavs/gt/zero_16k"
        sr = "16000"
        if not os.path.isdir(out_dir):
            os.makedirs(out_dir)
        multiTask.multiThread_use_multiprocessing_multiarg(
            scpTools.genscp_in_list(in_dir), 5, downSample_scp, in_dir,
            out_dir, sr)
    elif mode == 7:
        wav_path = "/home/work_nfs5_ssd/hzli/data/big_data/trimmed_wavs/SH-TenXiaozhi-20spk_020_000500.wav"
        out = get_wav_sample(wav_path)
        print(out)
    elif mode == 10:
        in_dir = "/home/backup_nfs2/data-TTS/Hi-Fi_TTS/hi_fi_tts_v0/audio"
        out_dir = "/home/backup_nfs2/data-TTS/Hi-Fi_TTS/hi_fi_tts_v0/wav"

        names1 = dirTools.get_all_dir(in_dir)
        for name1 in tqdm(names1):
            in1 = os.path.join(in_dir, name1)
            out1 = os.path.join(out_dir, name1)
            if not os.path.isdir(out1):
                os.mkdir(out1)

            names2 = dirTools.get_all_dir(in1)
            for name2 in names2:
                in2 = os.path.join(in1, name2)
                out2 = os.path.join(out1, name2)
                if not os.path.isdir(out2):
                    os.mkdir(out2)

                flac2wav(in2, out2)
    elif mode == 11:
        # in_dir = "/home/backup_nfs4/data-TTS/m4singer/m4singer"
        # in_dir = "/home/backup_nfs4/data-TTS/nus48e/nus-smc-corpus_48"
        # in_dir = "/home/backup_nfs4/data-TTS/NHSS/F01/S01"
        # in_dir = "/home/backup_nfs4/data-TTS/opensinger/OpenSinger"
        in_dir = '/home/backup_nfs2/data-TTS/dailytalk/dailytalk'

        outfile = "/home/work_nfs5_ssd/hzli/kkcode/tmp/data_example/dailytalk.xlsx"

        exclude_dirs = []
        # exclude_dirs = ["wav", "wav_16k", "wav_24k", "Speech"]
        # exclude_dirs = ['read']

        exclude_files = []
        # exclude_files = ['song', 'speech']

        export_wav_time_xlsx(in_dir,
                             outfile=outfile,
                             mode='-r',
                             exclude_dirs=exclude_dirs,
                             exclude_files=exclude_files)
    elif mode == 12:
        in_dir = "/home/work_nfs5_ssd/hzli/data/big_data/wavs"

        # outfile = "/home/work_nfs5_ssd/hzli/kkcode/workroom/20220924-biaobei/about_data2/wav_dur.xlsx"
        outfile = None

        export_wav_time_xlsx(in_dir, outfile=outfile, mode='')
    elif mode == 13:
        dir1 = "/home/work_nfs5_ssd/hzli/data/adapt/lhz/origin_wavs"
        dir2 = "/home/work_nfs5_ssd/hzli/data/adapt/lhz/origin_wavs_c1"
        multiTask.multiThread_use_multiprocessing_multiarg(
            scpTools.genscp_in_list(dir1), 2, wav_to_one_channel, dir1, dir2)
    elif mode == 14:
        utts = scpTools.scp2list(
            "/home/work_nfs5_ssd/hzli/data/testset/niren_test/demo_221103/file_lst/test.lst"
        )
        in_dir = "/home/work_nfs6/hzli/logdir/niren/20221101-niren_base_chat_F03M83M84_alltag_v2_concat_prenet/25w_will_concat"
        # in_dir = "/home/work_nfs6/hzli/logdir/niren/20221101-niren_base_chat_F03M83M84_alltag_v2/21w_concat"
        out_dir = "/home/work_nfs6/hzli/logdir/niren/20221101-niren_base_chat_F03M83M84_alltag_v2_concat_prenet/25w_concat_v4_1.wav"
        # out_dir = "/home/work_nfs6/hzli/logdir/niren/20221101-niren_base_chat_F03M83M84_alltag_v2/21w_concat.wav"
        concat_wav_by_scp_with_sil(in_dir, out_dir, utts)
    elif mode == 15:
        indir = "/home/work_nfs6/hzli/logdir/event_transfer/adaspeech/adaspeech_3_stage4_a"
        indirs = glob.glob(indir + '/syn_chat_stage4_27w6k*_24k')
        for dir1 in indirs:
            dir2 = dir1 + '_down16k'
            sr = "16000"
            multiTask.multiThread_use_multiprocessing_multiarg(
                scpTools.genscp_in_list(dir1), 20, downSample_scp, dir1, dir2, sr)
    elif mode == 16:
        utt2dur = find_wav_times('/home/work_nfs5_ssd/hzli/data/niren/transfer/trimmed_wavs', 
                                 scpTools.scp2list('/home/work_nfs5_ssd/hzli/data/niren/transfer/file_lst/train_03_1w.lst'))
        print(sum([float(utt2dur[i]) for i in utt2dur])/3600)

if (__name__ == "__main__"):
    main()

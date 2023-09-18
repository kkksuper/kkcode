import os
import numpy as np
import glob
from tqdm import tqdm
from scipy.interpolate import interp1d
from .  import labelTools, scpTools, durTools, wavTools, npTools, multiTask
from zhon.hanzi import punctuation
import string
import soundfile as sf

fix_punc = ',，？'

PUNCTUATION = list(punctuation + string.punctuation + fix_punc)  # 标点符号集合

def check_ttsing_label_phone(label_path):
    '''
    检查label的音素是否在实验室音素集中
    '''
    phone, pitch, slur, pho_pos_in_note, num, score_duration, real_duration, xmin, xmax = labelTools.read_label(
        label_path)
    _pad = '_'
    ttsing_phone_set = [_pad] + [
        'rest', 'm', 'ang', 'zh', 'e', 'uei', 'u', 't', 'ian', 'k', 'ong', 'd',
        'l', 'iou', 'x', 'ing', 'iang', 'n', 'z', 'sh', 'in', 'a', 'b', 'ai',
        'vn', 'uo', 'eng', 'i', 'ao', 'ch', 'en', 'g', 'uang', 'c', 'an', 'j',
        'h', 'q', 'v', 'uen', 'ie', 'iii', 'p', 'ii', 'iao', 's', 'uan', 'uai',
        'ou', 'ei', 'f', 'ia', 've', 'o', 'er', 'iong', 'r', 'ua', 'van', 'L',
        'EH', 'M', 'AH', 'N', 'TR', 'IY', 'ar', 'Z', 'T', 'S', 'AA', 'R', 'OW',
        'HH', 'G', 'IH', 'K', 'F', 'V', 'ER', 'TH', 'NG', 'W', 'B', 'EY', 'UW',
        'AO', 'AY', 'DH', 'D', 'Y', 'AE', 'P', 'uar', 'ianr', 'UH', 'SH', 'JH',
        'ueng', 'NT', 'ng', 'ruai'
    ]
    for i in range(len(phone)):
        if not phone[i] in ttsing_phone_set:
            print("error phone in {} : {}".format(i, phone[i]))


def check_np_by_load(in_dir, utts=None):
    '''
    检查 in_dir 下的 npy 文件能否被加载(未指定 utt 时为全部)
    '''
    if utts is None:
        utts = [
            os.path.splitext(os.path.basename(path))[0]
            for path in glob.glob(in_dir + "/*.npy")
        ]
    get = []
    for utt in tqdm(utts, desc='check_np_by_load'):
        try:
            tmp = np.load(os.path.join(in_dir, f'{utt}.npy'),
                          allow_pickle=False)
        except:
            print(f"error in: {utt}")
            get.append(utt)
            continue
    return get


def check_pitch_can_interp1d(in_dir, utts=None):
    '''
    检查 pitch_list（路径列表） 中所有 pitch 是否能被插值
    '''
    if utts is None:
        utts = [
            os.path.splitext(os.path.basename(path))[0]
            for path in glob.glob(in_dir + "/*.npy")
        ]
    get = []
    for utt in tqdm(utts, desc='check_pitch_can_interp1d'):
        try:
            pitch = np.load(os.path.join(in_dir, f'{utt}.npy'))
            assert len(pitch) > 0
            nonzero_ids = np.where(pitch != 0)[0]
            interp_fn = interp1d(
                nonzero_ids,
                pitch[nonzero_ids],
                fill_value=(pitch[nonzero_ids[0]], pitch[nonzero_ids[-1]]),
                bounds_error=False,
            )
            pitch = interp_fn(np.arange(0, len(pitch)))
        except:
            print(f"error in: {utt}")
            get.append(utt)
            continue
    return get


def check_mellen_wavlen(utt, 
                        mel_dir,
                        wav_dir,
                        sr=24000,
                        hop_size=300,
                        warn_value=10):
    '''
    比较 mel 上采样后与 wav 的采样点数的差异(采样点级), 默认警戒值 10 帧
    '''
    mel_len = npTools.mel_len(np.load(os.path.join(mel_dir, f"{utt}.npy")))
    wav_len = wavTools.get_wav_sample(os.path.join(wav_dir, f"{utt}.wav"), sr)
    diff = abs(wav_len - mel_len * hop_size)
    if diff > warn_value * hop_size:
        print(utt, diff)
    return diff


def check_mellens_wavlens(mel_dir,
                          wav_dir,
                          utts=None,
                          sr=24000,
                          hop_size=256,
                          warn_value=10):
    '''
    比较 mel 上采样后与 wav 的采样点数的差异(采样点级), 默认警戒值 10 帧
    '''
    if utts is None:
        utts = [
            os.path.splitext(os.path.basename(path))[0]
            for path in glob.glob(mel_dir + "/*.npy")
        ]
    diffs = []
    get = []
    warn_num = 0
    for utt in tqdm(utts):
        mel_len = npTools.mel_len(np.load(os.path.join(mel_dir, f"{utt}.npy")))
        wav_len = wavTools.get_wav_sample(os.path.join(wav_dir, f"{utt}.wav"),
                                          sr)
        diff = abs(wav_len - mel_len * hop_size)
        diffs.append(diff)
        if diff > warn_value * hop_size:
            warn_num += 1
            get.append(utt)
            print("diff more than {} : {} , diff is {}".format(
                warn_value, utt, diff))
    diffs = np.array(diffs)
    print("共计 {} 条, 平均差值: {}, 最大差值: {}, 最小差值: {}, 超出警戒值 {} 的 {} 条".format(
        len(utts), diffs.mean(), diffs.max(), diffs.min(), warn_value,
        warn_num))
    return get


def check_mellen_durlen(utt, mel_path, dur_path):
    '''
    比较 mel 和 dur 的长度差别
    '''
    dur = durTools.load_dur(os.path.join(dur_path, utt + ".lab"))
    dur_len = np.sum(dur)

    mel = np.load(os.path.join(mel_path, utt + ".npy"))
    mel_len = npTools.mel_len(mel)

    return dur_len, mel_len


def check_mellens_durlens(mel_path, dur_path, warn_value=10):
    '''
    比较并输出两个文件夹下mel和dur的长度差别, 返回超过 warn_value 的 utt list
    '''
    durs = [
        os.path.splitext(os.path.basename(i))[0]
        for i in glob.glob(dur_path + "/*.lab")
    ]
    mels = [
        os.path.splitext(os.path.basename(i))[0]
        for i in glob.glob(mel_path + "/*.npy")
    ]

    diffs = []
    get = []
    num = 0
    warn_num = 0

    for mel in tqdm(mels):
        if mel in durs:
            num += 1
            dur_len, mel_len = check_mellen_durlen(mel, mel_path, dur_path)
            diff = abs(dur_len - mel_len)
            diffs.append(diff)

            # 达到警戒值时报错
            if diff > warn_value:
                warn_num += 1
                get.append(mel)
                print(dur_len, mel_len)
                print("diff more than {} : {} , diff is {}".format(
                    warn_value, mel, diff))

    diffs = np.array(diffs)
    # np.savetxt("/home/work_nfs5_ssd/hzli/kkcode/tmp/dur_diff.txt", diffs)
    print("共计 {} 条, 平均差值: {}, 最大差值: {}, 最小差值: {}, 超出警戒值 {} 的 {} 条".format(
        num, diffs.mean(), diffs.max(), diffs.min(), warn_value, warn_num))
    return get



def check_wavlen_durlen(utt, wav_path, dur_path, sr, hop_size):
    '''
    比较 wav 和 dur 的长度差别
    '''
    dur = durTools.load_dur(os.path.join(dur_path, utt + ".lab"))
    dur_len = np.sum(dur)
    
    wav_len = wavTools.get_wav_frame(os.path.join(wav_path, utt + ".wav"), sr, hop_size)

    return dur_len, wav_len


def check_wavlens_durlens(wav_path, dur_path, warn_value=10, sr=24000, hop_size=256, utts=None):
    '''
    比较并输出两个文件夹下mel和dur的长度差别, 返回超过 warn_value 的 utt list
    '''
    if utts is None:
        durs = [
            os.path.splitext(os.path.basename(i))[0]
            for i in glob.glob(dur_path + "/*.lab")
        ]
        wavs = [
            os.path.splitext(os.path.basename(i))[0]
            for i in glob.glob(wav_path + "/*.wav")
        ]
        utts = scpTools.and_scp(durs, wavs) 

    diffs = []
    get = []
    num = 0
    warn_num = 0

    for utt in tqdm(utts):
        num += 1
        dur_len, wav_len = check_wavlen_durlen(utt, wav_path, dur_path, sr, hop_size)
        diff = abs(dur_len - wav_len)
        diffs.append(diff)

        # 达到警戒值时报错
        if diff > warn_value:
            warn_num += 1
            get.append(utt)
            print(dur_len, wav_len)
            print("diff more than {} : {} , diff is {}".format(
                warn_value, utt, diff))

    diffs = np.array(diffs)
    # np.savetxt("/home/work_nfs5_ssd/hzli/kkcode/tmp/dur_diff.txt", diffs)
    print("共计 {} 条, 平均差值: {}, 最大差值: {}, 最小差值: {}, 超出警戒值 {} 的 {} 条".format(
        num, diffs.mean(), diffs.max(), diffs.min(), warn_value, warn_num))
    return get


def check_wav_sr(in_dir, target_sr, utts=None):
    '''
    检查路径下 utts 对应的 wav 的采样率是否是 target_sr, 返回不是的 name list
    '''
    if utts is None:
        utts = [
            os.path.splitext(os.path.basename(path))[0]
            for path in glob.glob(in_dir + "/*.wav")
        ]
    srs = wavTools.get_wavs_sr(in_dir, utts)
    srs = np.array(srs)
    utts = np.array(utts)
    names = utts[np.where(srs != target_sr)]
    return names.tolist()


def check_nplen_lablen(utt, np_dir, lab_dir, np_dim=0):
    '''
    返回 numpy 的第 dim 维长度与 lab 行数
    '''
    np_len = np.load(os.path.join(np_dir, "{}.npy".format(utt))).shape[np_dim]
    lab_len = len(
        labelTools.read_label(os.path.join(lab_dir, "{}.lab".format(utt)))[0])
    return np_len, lab_len


def check_nplens_lablens(np_dir, lab_dir, utts=None, np_dim=0, maxnum=None):
    '''
    检查 numpy 的第 dim 维长度与 lab 行数的差别, maxnum 为输出的最大数量，缺省为全部输出
    '''
    if utts is None:
        utts = [
            os.path.splitext(os.path.basename(path))[0]
            for path in glob.glob(np_dir + "/*.npy")
        ]
    diffs = []
    get = []
    warn_num = 0
    for utt in tqdm(utts):
        np_len, lab_len = check_nplen_lablen(utt, np_dir, lab_dir, np_dim)
        diff = str(abs(np_len - lab_len))
        diffs.append(diff)
        if diff != 0:
            warn_num += 1
            get.append(utt)
            print("diff {} {}".format(utt, diff))
        if (maxnum is not None) and warn_num > maxnum:
            break
    diffs = np.array(diffs)
    print("共计 {} 条, 平均差值: {}, 最大差值: {}, 最小差值: {}, 超出警戒的 {} 条".format(
        len(utts), diffs.mean(), diffs.max(), diffs.min(), warn_num))
    return get


def check_lablens_durlens(lab_path, dur_path):
    '''
    比较并输出两个文件夹下lab和dur的长度差别
    '''
    durs = [
        os.path.splitext(os.path.basename(i))[0]
        for i in glob.glob(dur_path + "/*.lab")
    ]
    labs = [
        os.path.splitext(os.path.basename(i))[0]
        for i in glob.glob(lab_path + "/*.lab")
    ]
    output = []
    num = 0
    for lab in tqdm(labs):
        if lab in durs:
            num += 1
            lab_len = len(
                labelTools.read_label(
                    os.path.join(lab_path, "{}.lab".format(lab)))[0])
            dur_len = len(
                labelTools.read_label(
                    os.path.join(dur_path, "{}.lab".format(lab)))[0])
            diff = str(abs(dur_len - lab_len))
            if diff != '0':
                output.append(lab + ": " + diff)

    print("num:{}".format(num))
    print('\n'.join(output))


def check_wav_punc_issil_by_energy(utts, lab_dir, dur_dir, energy_dir, warning_value=10):
    '''
    用时长，找到标点和 sil 处对应的能量值，如果能量值大于警戒线，返回超过警戒线的 label 名称，所在行数，所在帧（始末），最大能量值
    '''
    infos = []
    total_punc_num = 0
    for utt in tqdm(utts):
        duration = durTools.load_dur(os.path.join(dur_dir, f'{utt}.lab'))
        energy = np.load(os.path.join(energy_dir, f'{utt}.npy'))
        phone = labelTools.read_label(os.path.join(lab_dir, f'{utt}.lab'))[0]
        punc_phone = [pho for pho in phone if pho in PUNCTUATION]
        total_punc_num += len(punc_phone)

        assert len(phone) == len(duration), f'utt {utt} lab and duration is not same len, lab {len(phone)}, duration {len(duration)}'

        cur_dur = 0
        for i, (pho, dur) in enumerate(zip(phone, duration)):
            cur_energy = energy[cur_dur: cur_dur+dur+1]
            if pho in PUNCTUATION and np.max(cur_energy) >= warning_value:
                infos.append([utt, i, cur_dur, cur_dur+dur, cur_energy.tolist(), np.max(cur_energy)])
            cur_dur += dur
    print(f'标点数：{total_punc_num}，超过警戒的标点数：{len(infos)}')
    return infos
    

def check_wav_by_sfread(in_dir, utts=None):
    '''
    检查 in_dir 下的 wav 文件能否被 soundfile 加载(未指定 utt 时为全部)
    '''
    if utts is None:
        utts = [
            os.path.splitext(os.path.basename(path))[0]
            for path in glob.glob(in_dir + "/*.wav")
        ]
    get = []
    for utt in tqdm(utts, desc='check_wav_by_sfread'):
        try:
            tmp = sf.read(os.path.join(in_dir, f'{utt}.wav'))
        except:
            print(f"error in: {utt}")
            get.append(utt)
            continue
    return get



def main():

    mode = 12

    if mode == 0:
        pitch_dir = "/home/work_nfs5_ssd/hzli/data/biaobei/chat-emotion/pitches"
        check_pitch_can_interp1d(pitch_dir)
    elif mode == 1:
        np_dir = "/home/work_nfs5_ssd/hzli/data/big_data/pitches"
        check_np_by_load(np_dir)
    elif mode == 3:
        label_path = "/home/work_nfs5_ssd/hzli/kkcode/tmp1/116.lab"
        check_ttsing_label_phone(label_path)
    elif mode == 4:
        mel_path = "/home/work_nfs6/ypjiang/data/finetune/mels"
        dur_path = "/home/work_nfs6/ypjiang/data/finetune/durs"
        check_mellens_durlens(mel_path, dur_path)
    elif mode == 6:
        utts = scpTools.scp2list(
            "/home/work_nfs4_ssd/hzli/data/multi-bigdata-AM3-16k-gta/file_lst/all_delete_nogta_noorigin.lst"
        )
        utts = ["shannon_real_child_neutral_raw_105938"]
        mel_dir = "/home/work_nfs4_ssd/hzli/data/multi-bigdata-AM3-16k-gta/mels"
        wav_dir = "/home/work_nfs4_ssd/hzli/data/multi-bigdata-AM3-16k-gta/trimmed_wavs"
        hop_size = 300
        check_mellens_wavlens(mel_dir, wav_dir, utts, hop_size)
    elif mode == 7:
        utts = scpTools.scp2list(
            "/home/work_nfs4_ssd/hzli/data/multi-bigdata-AM3-16k-gta/file_lst/all_delete_nogta_noorigin.lst"
        )
        # utts = [i for i in utts if not i.endswith('_gta')]
        mel_dir = "/home/work_nfs4_ssd/hzli/data/multi-bigdata-AM3-16k-gta/mels"
        wav_dir = "/home/work_nfs4_ssd/hzli/data/multi-bigdata-AM3-16k-gta/trimmed_wavs"
        hop_size = 300
        ex = {"mel_dir": mel_dir, "wav_dir": wav_dir, "hop_size": hop_size}
        diffs = multiTask.multiThread_use_ProcessPoolExecutor_dicarg(
            utts, 80, check_mellen_wavlen, ex)
        diffs = np.array(diffs)
        warn_value = hop_size * 10
        warn_num = np.where(diffs > warn_value)[0]
        warn_num = len(warn_num)
        print("共计 {} 条, 平均差值: {}, 最大差值: {}, 最小差值: {}, 超出警戒值 {} 的 {} 条".format(
            len(utts), diffs.mean(), diffs.max(), diffs.min(), warn_value,
            warn_num))
    elif mode == 8:
        mel_path = "/home/work_nfs5_ssd/hzli/data/niren/220924/mels/"
        dur_path = "/home/work_nfs5_ssd/hzli/data/niren/220924/durs/"
        name = "F0312001001"
        print(check_mellen_durlen(name, mel_path, dur_path))
    elif mode == 9:
        mel_path = "/home/work_nfs5_ssd/hzli/data/aslp10j/mels/"
        dur_path = "/home/work_nfs5_ssd/hzli/data/aslp10j/durs_kaldi/"
        check_mellens_durlens(mel_path, dur_path)
    elif mode == 10:
        lab_path = "/home/work_nfs5_ssd/hzli/data/biaobei/chat/labs_v3_with_rest_speed/"
        dur_path = "/home/work_nfs5_ssd/hzli/data/biaobei/chat/durs_htk_rest/"
        check_lablens_durlens(lab_path, dur_path)
    elif mode == 11:
        out = check_wav_sr("/home/backup_nfs2/data-TTS/EmoV_DB/all", 16000)
        print(len(out))
    elif mode == 12:
        get = check_wavlens_durlens("/home/work_nfs5_ssd/hzli/data/big_data/trimmed_wavs/", "/home/work_nfs7/ykli/data/vits/bigdata/durs",
                              sr=24000, hop_size=300, utts=scpTools.scp2list('/home/work_nfs4_ssd/ykli/data/vits/big_data/all2.lst'))
        scpTools.list2scp(get, '/home/work_nfs5_ssd/hzli/kkcode/tmp/error.lst')


if __name__ == "__main__":
    main()

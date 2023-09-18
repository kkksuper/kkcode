import math
import os
import numpy as np
import glob
from tqdm import tqdm
import traceback
from sklearn.metrics.pairwise import cosine_similarity
from . import jsonTools, scpTools
import json


def mel_len(mel):
    '''
    输入np数组，返回mel的长度
    '''
    return mel.shape[0] if mel.shape[1] == 80 else mel.shape[1]


def see_np(in_dir, print_detail=False, max_len=None):
    '''
    打印in_dir的np，可选是否打印具体的值，以及打印的话输出的最大行数（默认无穷）
    '''
    f = np.load(in_dir)
    print(f.shape)
    if print_detail:
        np.set_printoptions(threshold=np.inf if max_len is None else max_len)
        print(f)
    return f.shape


def init_np_zeros_from_durs(utts, dur_dir, out_dir):
    '''
    根据时长文件，初始化全 0 的 np，并输出到对应路径
    '''
    for utt in tqdm(utts):
        dur_path = os.path.join(dur_dir, f"{utt}.lab")
        duration = np.sum(np.sum(np.loadtxt(dur_path), axis=1))
        out = np.zeros(int(duration))
        np.save(os.path.join(out_dir, f"{utt}"), out)


def npT(in_dir, out_dir, utts=None):
    '''
    将 in_dir 下的所有 npy 文件进行转置，并输出到 out_dir
    '''
    if not os.path.isdir(out_dir):
        os.mkdir(out_dir)
    if utts is None:
        utts = [os.path.splitext(os.path.basename(path))[0] for path in glob.glob(in_dir + "/*.npy")]
    for utt in tqdm(utts):
        tmp = np.load(os.path.join(in_dir, utt + '.npy'))
        np.save(os.path.join(out_dir, utt), tmp.T)


def get_melshape(in_dir, scp):
    '''
    扫描indir中，在scp中的np文件，返回dict[mel]=mel_len(mel)
    '''
    utt2shape = {}

    for mel in tqdm(scp):
        try:
            tmp = np.load(os.path.join(in_dir, mel + ".npy"))
            utt2shape[mel] = mel_len(tmp)
        except:
            print(mel)
            continue

    return utt2shape


def calc_np_minmax(utts, np_dir):
    mmin = float('inf')
    mmax = float('-inf')
    for utt in tqdm(utts):
        tmp = np.load(os.path.join(np_dir, f"{utt}.npy"))
        mmin = min(tmp.min(), mmin)
        mmax = max(tmp.max(), mmax)
    print(f"min:{mmin}, max:{mmax}")
    return mmin, mmax


def find_short_npy(utt2shape, scp, minlen=64):
    '''
    根据utt2shape，筛选 scp 中过短的mel，打印总数目并返回 name list
    '''
    num = 0
    short_list = {}

    for mel in tqdm(scp):
        if utt2shape[mel] <= minlen:
            num += 1
            short_list[mel] = utt2shape[mel]

    print("complete find short, total short num: " + str(num))
    return short_list


def find_long_npy(utt2shape, scp, maxlen=2000):
    '''
    根据utt2shape，筛选 scp 中过长的mel，打印总数目并返回 name list
    '''
    num = 0
    long_list = {}

    for mel in tqdm(scp):
        if utt2shape[mel] >= maxlen:
            num += 1
            long_list[mel] = utt2shape[mel]

    print("complete find long, total long num: " + str(num))
    return long_list

def sum_npy_len(utt2shape, scp):
    '''
    根据utt2shape，统计总帧数
    '''
    num = 0
    dur = 0
    for mel in tqdm(utt2shape):
        if mel not in utt2shape:
            continue
        num += 1
        dur += utt2shape[mel]

    print(f"total num:{num}, total dur:{dur}")
    return num    


def find_shortest_mel(in_dir):
    '''
    根据utt2shape，找到 scp 中最短的 mel, 打印并返回其name和长度
    '''
    mels = [
        os.path.splitext(os.path.basename(i))[0]
        for i in glob.glob(in_dir + "/*.npy")
    ]
    min = "0"
    minlen = float("inf")

    for mel in tqdm(mels):
        mellen = mel_len(np.load(os.path.join(in_dir, mel + ".npy")))
        minlen = mellen if mellen < minlen else minlen
        min = mel if mellen < minlen else min

    print(min, minlen)
    return min, minlen


def find_longest_mel(in_dir):
    '''
    找到目录下最长的mel, 打印并返回其name和长度
    '''
    mels = [
        os.path.splitext(os.path.basename(i))[0]
        for i in glob.glob(in_dir + "/*.npy")
    ]
    max = "0"
    maxlen = float("inf")

    for mel in tqdm(mels):
        mel_len = mel_len(np.load(os.path.join(in_dir, mel + ".npy")))
        maxlen = mel_len if mel_len > maxlen else maxlen
        max = mel if mel_len > maxlen else max

    print(max, maxlen)
    return max, maxlen


def align_mel(in_dir, in_utts, ref_dir, ref_utts, out_dir):
    '''
    根据ref_dir中mel的长度，将in_dir中的mel对齐(截取为较短长度)，输出到out_dir中
    '''
    os.makedirs(out_dir, exist_ok=True)

    for in_utt, ref_utt in tqdm(zip(in_utts, ref_utts)):
        try:
            in_mel = np.load(os.path.join(in_dir, in_utt + ".npy"))
            ref_mel = np.load(os.path.join(ref_dir, ref_utt + ".npy"))
            print(in_utt)
            print(in_mel.shape[1], ref_mel.shape[1])
            target_mel_frames = min(in_mel.shape[1], ref_mel.shape[1])
            in_mel = in_mel[:, :target_mel_frames]
            print(in_mel.shape[1])
            np.save(os.path.join(out_dir, in_utt), in_mel)
        except Exception as e:
            print("error: ", in_utt)
            traceback.print_exc()
            break

def sum_utt2mellen(utt2mellen):
    '''
    读取 utt2mellen.json，计算总帧数
    '''
    js = json.load(open(utt2mellen, 'r'))
    lens = 0
    for utt in js:
        lens += js[utt]
    return len(js), lens

def calc_cos(in_dir1, ref_np, utts=None):
    '''
    计算路径下的 np 和目标 np 的 cos
    '''
    b = np.load(ref_np)
    if utts is None:
        utts = scpTools.genscp_in_list(in_dir1)
    coss = []
    for utt in utts:
        a = np.load(os.path.join(in_dir1, f'{utt}.npy'))
        cos = cosine_similarity(a.reshape(1,-1),b.reshape(1,-1))
        coss.append(cos)
    coss = np.array(coss)
    return coss

def calc_cos_dirs(in_dir1, in_dir2, utts=None):
    '''
    计算两个路径下的 np cos
    '''
    if utts is None:
        utts = scpTools.genscp_in_list(in_dir1)
    coss = []
    for utt in utts:
        a = np.load(os.path.join(in_dir1, f'{utt}.npy'))
        b = np.load(os.path.join(in_dir2, f'{utt}.npy'))
        cos = cosine_similarity(a.reshape(1,-1),b.reshape(1,-1))
        coss.append(cos)
    return coss

def calc_pitch_std(utts, in_dir):
    '''
    统计 pitch 标准差，返回平均值
    '''
    std = []
    for utt in tqdm(utts):
        pitch = np.load(os.path.join(in_dir, f'{utt}.npy'))
        pitch = np.exp(pitch)
        std.append(np.std(pitch))
    return np.mean(np.array(std)), np.std(np.array(std))
    

def main():

    mode = 14

    if mode == 0:
        in_dir = "/home/work_nfs6/hzli/logdir/tmp/for_duk/16w_gl_tangshi_sty_5spk_0/02_1.npy"
        see_np(in_dir, True)
    elif mode == 1:
        in_dir = "/home/work_nfs4_ssd/hzli/data/17spks_woman/train/audio/SH-TenXiaozhi-20spk_020_000500.npy"
        see_np(in_dir, False)
    elif mode == 2:
        in_dir = "/home/work_nfs5_ssd/hzli/acoustic_model/nice-fs2/hzli_utils/thai/"
        out_dir = "/home/work_nfs5_ssd/hzli/acoustic_model/nice-fs2/hzli_utils/thaiT/"
        npT(in_dir, out_dir)
    elif mode == 3:
        in_dir = "/home/work_nfs5_ssd/hzli/data/didi_audition4spk/jiangzao/jiangzao_v2"
        find_long_npy(in_dir)
    elif mode == 4:
        in_dir = "/root/workspace/syn/last/conformer_M_3760_gt_dur_g_00835000/mels"
        ref_dir = "/data/fuxi_opensource_2_new/last_test/mels"
        out_dir = "/root/workspace/syn/last/conformer_M_3760_gt_dur_g_00835000/aligned_mels"
        align_mel(in_dir, ref_dir, out_dir)
    elif mode == 6:
        base_dir = "/home/work_nfs5_ssd/hzli/data/big_data"
        in_dir = os.path.join(base_dir, "mels")
        # in_dir = os.path.join("/home/work_nfs5_ssd/hzli/data/big_data", "mels")
        out_dir = os.path.join(base_dir, "utt2mellen.json")
        # scp = scpTools.scp2list(os.path.join(base_dir, "file_lst",
        #                                      "test.lst"))
        scp = scpTools.genscp_in_list(in_dir)
        renew = True
        if os.path.isfile(out_dir) and not renew:
            utt2mellen = json.load(open(out_dir))
        else:
            utt2mellen = get_melshape(in_dir, scp)
            jsonTools.save_json(utt2mellen, out_dir)
        name_list = find_long_npy(utt2mellen, scp, maxlen=1500)
        # name_list = find_short_npy(utt2mellen, scp, minlen=200)
        # scpTools.list2scp(name_list, os.path.join(base_dir, "file_lst", "all_morethan_1500.lst"))
        # scpTools.list2scp(name_list, os.path.join(base_dir, "all_lessthan_80.lst"))
        out = [str(i) + ":" + str(name_list[i]) for i in name_list]
        # out = [str(i) for i in name_list]
        print('\n'.join(out))
        # print(len(out))
        # print(len([i for i in out if i.startswith("db6_emotion")]))
    elif mode == 7:
        print(
            mel_len(
                np.load(
                    "/home/work_nfs6/dkguo/data/voice_clone/mels/CJ-2.npy")))
        print(
            mel_len(
                np.load(
                    "/home/work_nfs5_ssd/hzli/data/adapt/aslp10j/mels/CJ-2.npy"
                )))
    elif mode == 8:
        in_dir = "/home/work_nfs6/hzli/logdir/biaobei/20220927-biaobei_base_chat_F03M83M84/221014_spk28"
        in_dir = "/home/work_nfs6/dkguo/workspace/nice-xfzhu/nice/conformer/egs/multispksty/from_zero/16w_gl_tangshi_sty_5spk_0"
        utts = scpTools.genscp_in_list(in_dir)
        utts = set(utts)
        print(in_dir)
        calc_np_minmax(utts, in_dir)
    elif mode == 9:
        in_dir = "/home/work_nfs5_ssd/hzli/data/db6/mels"
        find_shortest_mel(in_dir)
    elif mode == 10:
        in_dir = "/home/work_nfs5_ssd/hzli/data/niren/with_db6/durs"
        out_dir = "/home/work_nfs5_ssd/hzli/data/niren/with_db6/frame_modal_smile_tag"
        utts = scpTools.scp2list(
            "/home/work_nfs5_ssd/hzli/data/niren/with_db6/file_lst/db6_neutral.lst"
        )
        init_np_zeros_from_durs(utts, in_dir, out_dir)
    elif mode == 11:
        num, lens = sum_utt2mellen('/home/work_nfs5_ssd/hzli/data/big_data/utt2mellen.json')
        print(num, 1.0 / 24000 * 256 * lens / 60 / 60)
    
    elif mode == 12:
        utt2mellen = json.load(open('/home/work_nfs5_ssd/hzli/data/big_data/utt2mellen.json'))
        sum_npy_len(utt2mellen, scpTools.scp2list("/home/work_nfs7/lhma/bigdata/data/filelist_filted_less1500.lst"))
        
    elif mode == 13:
        # 看看目录下所有 np 的长度
        in_dir = ''
        utts = scpTools.genscp_in_list(in_dir)
        l =  []
        for utt in utts:
            l.append(see_np(os.path.join(in_dir, f'{utt}.npy')))
        output = ['\t'.join(i,j) for i,j in zip(utts, l)]
        scpTools.list2scp(output, '/home/work_nfs5_ssd/hzli/kkcode/tmp/tmp.lst')
    
    elif mode == 14:
        '''
        db6
        dio f0 (112.60355652491401, 7.196569814459747)
        harveest lf0 (1.8021565148966754, 0.2627515629135113)
        harvest f0 (85.46461706086036, 11.488476661852248)
        f03
        dio f0 (113.00395399650415, 13.129731251666435)
        harveest lf0 (1.8021565148966754, 0.2627515629135113)
        harvest f0 (93.96536270656385, 17.199578880233748)
        '''
        in_dir = '/home/work_nfs5_ssd/hzli/data/niren/transfer/pitches_harvest'
        utts = scpTools.scp2list('/home/work_nfs5_ssd/hzli/data/niren/transfer/file_lst/train_db6_1w.lst')
        # utts = scpTools.scp2list('/home/work_nfs5_ssd/hzli/data/niren/transfer/file_lst/train_03_1w.lst')
        print(in_dir)
        print(calc_pitch_std(utts, in_dir))
            


if __name__ == "__main__":
    main()

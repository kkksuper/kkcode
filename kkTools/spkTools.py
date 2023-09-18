import json
from tqdm import tqdm
from typing import Tuple
from . import scpTools, jsonTools


def gen_utt2spk_all(utts, out_path, spk_name):
    """
      将数据路径下所有文件指定为spk_name说话人，并生成utt2spk
    """
    f_out = open(out_path, "w")

    for utt in utts:
        f_out.write(utt + "\t" + spk_name + "\n")

    f_out.flush()
    f_out.close()


def gen_utt2spk(utts, out_dir, start2spk, else_name=None, assert_else=False):
    '''
    根据 start2spk 判断每个文件名属于哪个说话人，并在 out_dir 下生成 utt2spk, 如果都不属于，可以指定为 else name, 如果属于多个 start 则认定为第一个 start
    '''
    f_out =  open(out_dir, 'w')
    utt2spk = []

    for utt in utts:
        inelse = True
        for start in start2spk:
            if utt.startswith(start):
                inelse = False
                utt2spk.append(utt + "\t" + start2spk[start])
                break
        if inelse:
            if else_name is not None:
                utt2spk.append(utt + "\t" + else_name)
            elif assert_else:
                print(utt)
                exit()
    
    f_out.write('\n'.join(utt2spk))
    f_out.flush()
    f_out.close()


def get_spks_by_name_id(name, ids):
    '''
    根据数据集名称以及说话人id, 拼接得到spks
    '''
    return [name + id for id in ids]


def gen_spk2num_by_spkstart(scp: list, spks: list) -> Tuple[dict, list]:
    '''
    根据文件名列表和每个spk对应的文件名开头, 得到每个spk的文件数, 以及不是这些说话人的文件list
    '''
    spk2num = {}
    other = []

    for spk in spks:
        spk2num[spk] = 0
    
    for f in tqdm(scp):
        isother = True
        for spk in spks:
            if f.startswith(spk):
                spk2num[spk] += 1
                isother = False
                break
        if isother:
            other.append(f)
    
    return spk2num, other


def gen_spk2id(spks, out_dir, start_id=0):
    '''
    根据spks list，生成spk2id
    '''
    spk2id = {}
    id = start_id

    for spk in spks:
        spk2id[spk] = id
        id += 1
    
    jsonTools.save_json(spk2id, out_dir)


def load_utt2spk(utt2spk_path):
    '''
    读取utt2spk，返回字典
    '''
    utt2spk = {}
    with open(utt2spk_path, encoding='utf-8') as f:
        for line in f.readlines():
            utt, spk = line.strip().split("\t")
            utt2spk[utt] = spk
    return utt2spk


def trans_utt2spk_to_spk2utt(utt2spk):
    '''
    输入 utt2spk 字典，输出 spk2utt 字典
    '''
    spk2utt = {}
    for utt in utt2spk:
        spk = utt2spk[utt]
        if spk in spk2utt:
            spk2utt[spk].append(utt)
        else:
            spk2utt[spk] = [utt]
    return spk2utt


def get_spk2num_from_spk2utt(spk2utt):
    '''
    从 spk2utt 中得到 spk2num
    '''
    spk2num = {}
    for spk in spk2utt:
        spk2num[spk] = len(spk2utt[spk])
    return spk2num


def trans_spk2utt_to_utt(spk2utt):
    '''
    将 spk2utt 转为 utt
    '''
    utts = []
    for spk in spk2utt:
        utts.extend(spk2utt[spk]) 
    return utts


def gen_spk2emo(utt2spk, utt2emo):
    '''
    根据输入的 utt2spk 和 utt2emo，得到 spk2emo
    '''
    spk2emo = {}
    utt2spk = load_utt2spk(utt2spk)
    utt2emo = load_utt2spk(utt2emo)
    for utt in utt2spk:
        if utt not in utt2emo:
            continue
        spk = utt2spk[utt]
        emo = utt2emo[utt]
        if spk not in spk2emo:
            spk2emo[spk] = []
        spk2emo[spk].append(emo)

    for spk in spk2emo:
        spk2emo[spk] = list(set(spk2emo[spk]))
    
    return spk2emo
            
def get_spk_map(spk2id_path, utt2spk_path):
    '''
    输入 spk2id 路径 和 utt2spk 路径\n
    得到 spk2id 和 utt2spk    
    '''
    utt2spk = {}
    with open(spk2id_path, "r") as spk2id_file:
        spk2id = json.load(spk2id_file)
    with open(utt2spk_path, encoding='utf-8') as f:
        for line in f.readlines():
            utt, spk = line.strip().split("\t")
            utt2spk[utt] = spk
    return spk2id, utt2spk


def main():

    mode = 2

    if mode == 0:
        utts = scpTools.scp2list("/home/work_nfs5_ssd/hzli/data/big_data/file_lst/train.lst")
        out_dir = "/home/work_nfs5_ssd/hzli/data/big_data/adapt/asr_syliu_4spk/utt2spk"
        spks = ["shannon_real_child_neutral", "shannon_neutral", "male_raw", "db_1_new"]
        start2spk = {spk:spk for spk in spks}
        gen_utt2spk(utts, out_dir, start2spk)
    elif mode == 1:
        data_dir = "/home/work_nfs5_ssd/hzli/data/biaobei/kefu/file_lst/all.lst"
        out_dir = "/home/work_nfs5_ssd/hzli/data/biaobei/kefu/utt2emo"
        gen_utt2spk_all(scpTools.scp2list(data_dir), out_dir, "kefu")
    elif mode == 2:
        spks = ["shannon_real_child_neutral", "shannon_neutral", "male_raw", "db_1_new"]
        out_dir = "/home/work_nfs5_ssd/hzli/data/big_data/adapt/asr_syliu_4spk/spk2id.json"
        gen_spk2id(spks, out_dir)
    elif mode == 3:
        utts = scpTools.scp2list("/home/work_nfs5_ssd/hzli/kkcode/tmp/utt_2000")
        exclude = scpTools.scp2list("/home/work_nfs5_ssd/hzli/kkcode/tmp/exclude.log")
        new_utts = list(set(utts).difference(set(exclude)))  # utts中有而exclude中没有的
        print('\n'.join(new_utts))
    elif mode == 4:
        utts = scpTools.scp2list("/home/work_nfs5_ssd/hzli/kkcode/tmp/same_durs_mels.log")
        spks = scpTools.scp2list("/home/work_nfs5_ssd/hzli/kkcode/tmp/spks")
        spk2num, others = gen_spk2num_by_spkstart(utts, spks)
        print(spk2num)
        # others.sort()
        # print('\n'.join(others))
    elif mode == 5:
        utt2spk = load_utt2spk("/home/work_nfs5_ssd/hzli/kkcode/tmp_hw/utt2spk")
        spk2utt = trans_utt2spk_to_spk2utt(utt2spk)
        jsonTools.save_json(spk2utt, "/home/work_nfs5_ssd/hzli/kkcode/tmp_hw/spk2utt")
    elif mode == 6:
        spks = ["angry", "sad", "encourage", "happy", "disgust", "surprise", "coquetry", "adore", "neutral", "chat", "kefu"]
        out_dir = "/home/work_nfs5_ssd/hzli/data/biaobei/emo2id.json"
        gen_spk2id(spks, out_dir, 0)
    elif mode == 7:
        utts = scpTools.genscp_in_list("/home/work_nfs5_ssd/hzli/data/biaobei/chat-emotion/mels/")
        out_dir = "/home/work_nfs5_ssd/hzli/data/biaobei/chat-emotion/utt2emo"
        start2spk={
            "8401":"kefu",
            "F10":"kefu",
            "8313":"neutral",
            "0313":"neutral",
            "8412":"neutral",
            "8413":"neutral",
            "M8312":"chat",
            "F0312":"chat",
            "8317":"angry",
            "8319":"sad",
            "8315":"encourage",
            "8316":"happy",
            "0316":"happy",
            "0320":"disgust",
            "0318":"surprise",
            "0314":"coquetry",
            "0321":"adore",
            "0317":"angry",
            "0319":"sad",
            "0315":"encourage",
            "8415":"encourage",
            "8417":"angry",
            "8416":"happy",
            "8419":"sad"
        }
        gen_utt2spk(utts, out_dir, start2spk)
    elif mode == 8:
        utts = scpTools.genscp_in_list("/home/work_nfs5_ssd/hzli/data/biaobei/kefu/txts/")
        out_dir = "/home/work_nfs5_ssd/hzli/data/biaobei/kefu/utt2spk"
        start2spk={
            "84":"84",
            "10":"10",
            "F10":"10",
            "8313":"83",
            "0313":"03",
            "M8312":"83",
            "F0312":"03",
            "8317":"83",
            "8319":"83",
            "8315":"83",
            "8316":"83",
            "0316":"03",
            "0320":"03",
            "0318":"03",
            "0314":"03",
            "0321":"03",
            "0317":"03",
            "0319":"03",
            "0315":"03"
        }
        gen_utt2spk(utts, out_dir, start2spk)
    elif mode == 9:
        utts = scpTools.genscp_in_list("/home/work_nfs5_ssd/hzli/data/hw_chat-db6_emo/mels/")
        out_dir = "/home/work_nfs5_ssd/hzli/data/hw_chat-db6_emo/utt2emo"
        start2spk={
            "F":"chat",
            "M":"chat",
            "db6_neutral":"neutral",
            "db6_emotion_angry":"angry",
            "db6_emotion_disgust":"disgust",
            "db6_emotion_fear":"fear",
            "db6_emotion_happy":"happy",
            "db6_emotion_sad":"sad",
            "db6_emotion_surprise":"surprise",
        }
        gen_utt2spk(utts, out_dir, start2spk)
    elif mode == 10:
        spk2emo = gen_spk2emo("/home/work_nfs7/lhma/bigdata/data/utt2spk", "/home/work_nfs7/lhma/bigdata/data/utt2emo")
        print(spk2emo)
    

if __name__ == "__main__":
    main()   

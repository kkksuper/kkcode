import math
import os
from tqdm import tqdm
import glob
import traceback
from functools import partial
from concurrent.futures import ProcessPoolExecutor

from zhon.hanzi import punctuation
import string
from . import scpTools, multiTask

fix_punc = ',，？'

PUNCTUATION = list(punctuation + string.punctuation + fix_punc)  # 标点符号集合

kInitialsList = [
    "b", "c", "ch", "d", "f", "g", "h", "j", "k", "l", "m", "n", "p", "q", "r",
    "s", "sh", "t", "x", "z", "zh"
]

kFinalsList = [
    "a", "ai", "an", "ang", "ao", "e", "ei", "en", "eng", "er", "iii", "ii",
    "i", "ia", "ian", "iang", "iao", "ie", "in", "ing", "iong", "iou", "o",
    "ong", "ou", "u", "ua", "uai", "uan", "uang", "uei", "uen", "ueng", "uo",
    "v", "van", "ve", "vn", "AA", "AE", "AH", "AO", "AW", "AX", "AXR", "AY",
    "EH", "EL", "EM", "EN", "ER", "EY", "IH", "IX", "IY", "OW", "OY", "UH",
    "UW", "X", "ar", "aor", "our", "or", "angr", "eir", "engr", "ianr", "iaor",
    "ingr", "iiir", "ongr", "uar", "uangr", "ur", "uenr", "uor", "iar", "ueir",
    "ir", "iir", "vanr", "vr", "air", "enr", "anr", "uanr", "ier", 'sil', 'sp',
    "SIL", "xr", "D"
]

PhoneCNList = [
    "n", "s", "iong", "h", "t", "c", "j", "ian", "x", "uan", "ou", "l", "e",
    "sh", "ang", "ong", "in", "iao", "ing", "z", "van", "uei", "ei", "i", "ch",
    "iang", "eng", "g", "ve", "ie", "q", "sil", "f", "uai", "k", "uo", "r",
    "m", "b", "o", "iou", "zh", "ao", "uang", "er", "d", "en", "a", "xr",
    "iii", "ua", "ueng", "ia", "v", "an", "L", "u", "ai", "ii", "p", "uen",
    "vn"
]
PhoneENList = [
    "ER", "AE", "HH", "S", "JH", "AY", "W", "DH", "SH", "AA", "EY", "T", "UH",
    "D", "AW", "OW", "K", "M", "P", "G", "AH", "Z", "IH", "N", "AO", "Y", "F",
    "ZH", "OY", "EH", "B", "V", "CH", "UW", "AX", "TH", "NG", "R", "IY"
]


def write_label(outpath, list_2d, seq='\t'):
    """
    从一个二维list中生成label \n
    list_2d中每一个list表示一个属性，且长度相等
    """
    # 如果不等于，则有重复数据
    a = [len(i) for i in list_2d]
    assert len(list(set(
        a))) == 1, f"label {outpath} attribute length is differrent {str(a)}"

    f = open(outpath, "w")

    for i in range(len(list_2d[0])):
        line = []
        for j in range(len(list_2d)):
            line.append(str(list_2d[j][i]).strip())
        row = seq.join(line)
        f.write(row + "\n")
    f.flush()
    f.close()


def read_label(label_path, seq='\t'):
    '''
    将一个label文件转为一个二维list, 每个属性一个list \n
    label不同属性用seq隔开
    '''
    lines = open(label_path, 'r', encoding="utf-8").readlines()
    num_attr = len(lines[0].split(seq))
    attrs = [[] for i in range(num_attr)]

    try:
        for line in lines:
            tmp = line.strip('\n').split(seq)
            for i in range(num_attr):
                attrs[i].append(tmp[i])
        return attrs
    except:
        print("eoor in: {}".format(label_path))
        traceback.print_exc()
        exit(0)


def get_lab_attrnum(label_path, seq='\t'):
    '''
    得到label一行有几种属性
    '''
    lines = open(label_path, 'r', encoding="utf-8").readlines()
    num_attr = len(lines[0].split(seq))
    return num_attr


def fix_spon_label(utt, lab_dir, out_dir):
    '''
    将含有 spon rest 列的标签：spon 改为 sp 0  S  3  N ，rest 列保留
    '''
    os.makedirs(out_dir, exist_ok=True)

    l1, l2, l3, l4, spon, rest = read_label(
        os.path.join(lab_dir, "{}.lab".format(utt)))

    add_index = []
    for id_tag, tag in enumerate(spon):
        if tag == 'S':
            add_index.append(id_tag)

    add_num = len(add_index)
    for i in range(add_num):
        l1.insert(add_index[-1 - i] + 1, 'sp')
        l2.insert(add_index[-1 - i] + 1, '0')
        l3.insert(add_index[-1 - i] + 1, 'S')
        l4.insert(add_index[-1 - i] + 1, '3')
        rest.insert(add_index[-1 - i] + 1, 'N')

    write_label(os.path.join(out_dir, "{}.lab".format(utt)),
                [l1, l2, l3, l4, rest])


def fix_label_add_tag(utt, in_dir, out_dir, fill_value):
    '''
    将原来的 label 后增加 fill_value list (每个元素一列)
    '''
    os.makedirs(out_dir, exist_ok=True)
    attrs = read_label(os.path.join(in_dir, "{}.lab".format(utt)))
    new_tag = [[fill] * len(attrs[0]) for fill in fill_value]
    attrs.extend(new_tag)
    write_label(os.path.join(out_dir, "{}.lab".format(utt)), attrs)

def fix_labels_add_tag(utts, in_dir, out_dir, fill_value):
    '''
    将原来的 label 后增加 fill_value list (每个元素一列)
    '''
    os.makedirs(out_dir, exist_ok=True)
    for utt in tqdm(utts):
        fix_label_add_tag(utt, in_dir, out_dir, fill_value)


def fix_label_del_tag(utts, in_dir, out_dir, del_num=None, back_num=None):
    '''
    将原来的 label 后删除最后 del_num 个属性，或者只保留 back_num 个属性，如果同时指定，则以 del num 为准
    '''
    assert del_num is not None and back_num is not None, "del num and back num not refer"
    os.makedirs(out_dir, exist_ok=True)
    for utt in tqdm(utts):
        attrs = read_label(os.path.join(in_dir, "{}.lab".format(utt)))
        if del_num is not None:
            attrs = attrs[:-1 * del_num]
        elif back_num is not None:
            attrs = attrs[:back_num + 1]
        write_label(os.path.join(out_dir, "{}.lab".format(utt)), attrs)


def fix_label_reset_tag(utts,
                        in_dir,
                        out_dir,
                        reset_index=None,
                        reset_value=None):
    '''
    将原来的 label 的 reset index 的 label 值，置为 reset value
    '''
    assert len(reset_index) == len(
        reset_value), "reset index length not match with reset value"
    os.makedirs(out_dir, exist_ok=True)
    for utt in tqdm(utts):
        attrs = read_label(os.path.join(in_dir, "{}.lab".format(utt)))
        for i, index in enumerate(reset_index):
            attrs[index] = [reset_value[i]] * len(attrs[0])
        write_label(os.path.join(out_dir, "{}.lab".format(utt)), attrs)


def fix_TTSlabel_backup4col(in_dir, out_dir):
    '''
    只保留label的前四列
    '''
    labels = glob.glob(in_dir + "/*.lab")
    labels.sort()

    if not os.path.isdir(out_dir):
        os.mkdir(out_dir)

    for label in tqdm(labels):
        attrs = read_label(label)

        out_path = os.path.join(out_dir, os.path.basename(label))
        write_label(out_path, [attrs[0], attrs[1], attrs[2], attrs[3]])


def compare_label_len(dir1, dir2, utts):
    '''
    比较两个目录下文件名为utts的lab的长度是否相同，返回不同的name_list
    '''
    diff = []
    for utt in tqdm(utts):
        len1 = get_label_len(os.path.join(dir1, utt + ".lab"))
        len2 = get_label_len(os.path.join(dir2, utt + ".lab"))
        if len1 != len2:
            diff.append(utt)
    return diff


def get_label_len(file):
    '''
    得到label长度
    '''
    len1 = len(open(os.path.join(file), 'r').readlines())
    return len1


def lab2txt(utt, lab_dir="", txt_dir=""):
    '''
    将lab第一列拼接，得到txt
    '''
    if not os.path.isfile(os.path.join(lab_dir, "{}.lab".format(utt))):
        return
    os.makedirs(txt_dir, exist_ok=True)
    text, _, _, _, _ = read_label(os.path.join(lab_dir, "{}.lab".format(utt)))
    text = ''.join(text)
    f_out = open(os.path.join(txt_dir, "{}.txt".format(utt)), 'w')
    f_out.write('{}\t{}\n'.format(utt, text))
    f_out.close()


def phone2syl(phone):
    '''
    将音素序列合并为音节序列，返回 （syl，[index...]） list
    '''
    syl = []
    tmp_phone = []
    tmp_index = []

    for i, p in enumerate(phone):
        tmp_phone.append(p)
        tmp_index.append(i)
        if p in kFinalsList or p == 'sil' or p in PUNCTUATION or \
            (i != len(phone) - 1 and ((phone[i] in PhoneCNList and phone[i+1] in PhoneENList) or (phone[i] in PhoneENList and phone[i+1] in PhoneCNList))):
            syl.append((''.join(tmp_phone), tmp_index))
            tmp_phone = []
            tmp_index = []
    return syl


def tag2syl(tag, syl, mode='first'):
    '''
    利用 phone2syl 函数输出的（syl，[index...]） list, 将音素级 tag 变为音节级（默认以音节第一个音素为准） \n
    将音素序列合并为音节序列，返回 （syl，[index...]） list \n
    mode: \n
    first 以第一个为准 \n
    average_int 数字取平均(取整) \n
    average_float 数字取平均(不取整) \n
    sum 数字求和 \n
    '''
    syl_tag = []

    for s_index, (s, p_index) in enumerate(syl):
        if mode == 'first':
            syl_tag.append(tag[p_index[0]])
        elif mode == 'sum':
            syl_tag.append(sum([tag[i] for i in p_index]))
        elif mode == 'average_int':
            syl_tag.append(sum([tag[i] for i in p_index]) // len(p_index))
        elif mode == 'average_float':
            syl_tag.append(1.0 * sum([tag[i] for i in p_index]) / len(p_index))
    return syl_tag


def judge_has_en_phone(utt, in_dir):
    '''
    检查 utt 有没有英文音素
    '''
    lab = read_label(
        os.path.join(in_dir, f"{utt}.lab"))

    phone = lab[0]
    for p in phone:
        if p[0] >= 'A' and p[0] <= 'Z':
            return True
    return False

def genlabel_single(txt_dir, lab_dir, scp_path, mode=0):
    '''
    调用前端，生成 label
    '''
    os.system(f"bash /home/work_nfs5_ssd/hzli/kkcode/bash/genlabel_notqueue_auto.sh {txt_dir} {lab_dir} {scp_path} {mode} >/dev/null 2>&1")

def genlabel_multi(txt_dir, lab_dir, tmp_scp_dir, utts=None, numthread=20, mode=0):
    '''
    调用 python 本身的多线程库，来生成 label
    '''
    os.makedirs(lab_dir, exist_ok=True)
    os.makedirs(tmp_scp_dir, exist_ok=True)
    if utts is None:
        utts = scpTools.genscp_in_list(txt_dir)
    
    lens = len(utts)
    len_per_scp = math.ceil(float(lens) / numthread)
    executor = ProcessPoolExecutor(max_workers=numthread)
    results = []

    for index in range(numthread):
        start_index = len_per_scp * index
        end_index = len_per_scp * (index + 1)
        end_index = end_index if end_index <= lens else lens + 1
        cur_scp = utts[start_index : end_index]
        cur_scp_path = os.path.join(tmp_scp_dir, f'scp-{index}.lst')
        scpTools.list2scp(cur_scp, cur_scp_path)
        results.append(executor.submit(partial(genlabel_single, txt_dir, lab_dir, cur_scp_path, mode)))
        
    return [result.result() for result in tqdm(results)]


def main():

    mode = 4

    if mode == 1:
        print(
            read_label(
                "/home/work_nfs5_ssd/hzli/data/big_data/clean_labels/AIIA_large_sample_4h_raw_a010096.lab"
            ))
    elif mode == 2:
        in_dir = "/home/work_nfs5_ssd/hzli/data/niren/transfer/clean_labels"
        out_dir = "/home/work_nfs5_ssd/hzli/data/niren/transfer/labs_events_fp"
        utts = scpTools.genscp_in_list(in_dir)
        print(len(utts))
        fix_labels_add_tag(utts, in_dir, out_dir,
                          ['N', 'N', 'N', 'N', 'N', '中', 'N'])
    elif mode == 3:
        utts = scpTools.scp2list(
            "/home/work_nfs4_ssd/hzli/data/duoyinzi/dataset_biaobei/file_lst/all.lst"
        )
        ex = {
            "lab_dir":
            "/home/work_nfs4_ssd/hzli/data/duoyinzi/dataset_biaobei/labs",
            "txt_dir":
            "/home/work_nfs4_ssd/hzli/data/duoyinzi/dataset_biaobei/txts_no_biaozhu"
        }
        multiTask.multiThread_use_ProcessPoolExecutor_dicarg(
            utts, 20, lab2txt, ex)
    elif mode == 4:
        lab = read_label(
            "/home/work_nfs4_ssd/ykli/data/vits/big_data/big-train.txt", '|'
        )
        utts, spkid, phos, durs, prosodys, tones = lab
        # print(lab[0])
        for i in tqdm(range(len(utts))):
            for d in durs[i]:
                if int(d) > 40:
                    print(utts[i])
                    break
    elif mode == 5:
        in_dir = "/home/work_nfs5_ssd/hzli/data/testset/niren_test/niren_test_221023/labs_with_rest_speed_liandu_emph_emotion_modal"
        out_dir = "/home/work_nfs5_ssd/hzli/data/testset/niren_test/niren_test_221023/labs_allN_with_rest_speed_liandu_emph_emotion_modal"
        os.makedirs(out_dir, exist_ok=True)
        utts = scpTools.genscp_in_list(in_dir)
        fix_label_reset_tag(utts,
                            in_dir,
                            out_dir,
                            reset_index=[4, 5, 6, 7, 8, 9],
                            reset_value=['N', 'N', 'N', 'N', 'N', 'N'])
    elif mode == 6:
        in_dir = '/home/work_nfs5_ssd/hzli/data/niren/220924/labs_with_rest_speed_liandu_emph_emotion_modal'
        out_dir = '/home/work_nfs5_ssd/hzli/data/niren/220924/labs_with_sp_4col'
        fix_TTSlabel_backup4col(in_dir, out_dir)
    elif mode == 7:
        syl = phone2syl(read_label("/home/work_nfs5_ssd/hzli/data/niren/220924/labs_with_rest_speed_liandu_emph_emotion_modal_dur+4/F03-M84-0313006100.lab")[0])
        print(syl)
    elif mode == 8:
        in_dir = "/home/work_nfs5_ssd/hzli/data/big_data/clean_labels"
        utts = scpTools.scp2list('/home/work_nfs5_ssd/hzli/data/big_data/file_lst/train.lst')
        get_utts = list(tqdm(filter(lambda utt: judge_has_en_phone(utt, in_dir), utts)))
        g_utts = scpTools.exclude_scp(utts, get_utts)
        scpTools.list2scp(g_utts, "/home/work_nfs5_ssd/hzli/data/big_data/file_lst/train_en.lst")
    elif mode == 9:
        genlabel_multi('/home/work_nfs5_ssd/hzli/data/genshin/processed_data/txts',
                       '/home/work_nfs5_ssd/hzli/data/genshin/processed_data/labs_test',
                       '/home/work_nfs5_ssd/hzli/data/genshin/processed_data/tmp')


if __name__ == "__main__":
    main()

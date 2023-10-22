import os
import math
import re
import random

def get_basename(path):
    '''
    根据路径，得到不含后缀的文件名 \n
    os.path.splitext(os.path.basename(path))[0]
    '''
    return os.path.splitext(os.path.basename(path))[0]

def is_start_in_list(filename, flist):
    '''
    判断文件名是否以flist中的一个为开头
    '''
    for i in flist:
        if filename.startswith(i):
            return True
    return False


def scp2list(scp_path):
    """
    读取scp文件，返回list \n
    即返回文件的每一行
    """
    assert os.path.isfile(scp_path), "scp path seems to be wrong: " + scp_path
    return [line.strip() for line in open(scp_path, "r").readlines()]


def list2scp(lst, out_path, sort=False):
    '''
    将list按行写入scp文件
    '''
    f = open(out_path, "w")
    
    if sort:
        lst.sort()
    
    f.write("\n".join(lst))

    f.flush()
    f.close()


def genscp_in_list(file_path, sort=False):
    '''
    统计路径下所有的文件名(不含后缀)，返回name list
    '''
    filenames = [
        os.path.splitext(os.path.basename(path))[0] for path in os.listdir(file_path)
    ]
    if sort:
        filenames.sort()
    return filenames


def genscp(file_path, out_path, sort=False):
    """
    统计路径下所有的文件名，写为scp文件(一行一个文件名)
    """
    filenames = [
        os.path.splitext(os.path.basename(path))[0] for path in os.listdir(file_path)
    ]

    if sort:
        filenames.sort()

    f = open(out_path, "w")
    f.write("\n".join(filenames))

    f.flush()
    f.close()


def utts2scp(utts, out_path):
    '''
    根据utts，在out_path中生成scp
    '''
    f = open(out_path, "w")
    f.write("\n".join(utts))

    f.flush()
    f.close()


def genscp_random(utts, get_num):
    """
    将输入的 utts 随机筛选 get num 条并返回
    """
    get = []

    random.shuffle(utts)

    for index, utt in enumerate(utts):
        if index >= get_num:
            break
        get.append(utt)

    return get


def genscp_select_random_by_start(utts, starts2num):
    """
    统计路径下所有的文件名，随机打乱后，取出以每个start开头num个utt，写入总的scp文件(一行一个文件名)
    """
    get = []
    random.shuffle(utts)

    for start in starts2num:
        num = 0
        for utt in utts:
            if utt.startswith(start):
                get.append(utt)
                num += 1
            if num == starts2num[start]:
                break
        if num < starts2num[start]:
            print(f'start {start} only has {num} utt, not enough for target {starts2num[start]}')

    return get


def genscp_divide_by_start_name(utts, out_path, name_list, write_all=False):
    """
    如果utt以name_list中某个为开头，则写入name对应的scp文件(name.lst)(一行一个文件名)，并生成总的name_list(all.lst)(可选)
    """
    if not os.path.isdir(out_path):
        os.mkdir(out_path)

    if write_all:
        sum = open(os.path.join(out_path, "all.lst"), 'w')

    for name in name_list:
        f_out = open(os.path.join(out_path, name+".lst"), 'w')

        for filename in utts:
            if filename.startswith(name):
                if write_all:
                    sum.write(filename + "\n")
                f_out.write(filename + "\n")

        f_out.flush()
        f_out.close()
    
    if write_all:
        sum.flush()
        sum.close()


def genscp_divide_by_start_auto(utts, out_path, auto_len=1):
    """
    用utt前 auto len 个字符来聚类，输出每一类的列表，写为 name.lst (一行一个文件名)
    """
    if not os.path.isdir(out_path):
        os.mkdir(out_path)

    scps = {}

    for utt in utts:
        if utt[:auto_len] not in scps:
            scps[utt[:auto_len]] = []
        scps[utt[:auto_len]].append(utt)
        

    for name in scps:
        f_out = open(os.path.join(out_path, name+".lst"), 'w')

        f_out.write('\n'.join(scps[name]))

        f_out.flush()
        f_out.close()


def genscp_divide_by_seq(utts, out_path, outname, num_scp):
    """
    统计路径下所有的文件名，按照数量同等划分，写为多个scp文件
    """
    if not os.path.isdir(out_path):
        os.mkdir(out_path)

    lens = len(utts)
    len_per_scp = math.ceil(float(lens) / num_scp)

    for index in range(num_scp):        
        start_index = len_per_scp * index
        end_index = len_per_scp * (index + 1)
        end_index = end_index if end_index <= lens else lens + 1
        cur_scp = utts[start_index : end_index]

        f = open(os.path.join(out_path, outname + "_" + str(index) + ".lst"), "w")
        f.write("\n".join(cur_scp))
        f.flush()
        f.close()


def genscp_train_test_by_start(utts, train_path, test_path, test_list):
    """
    统计路径中的所有的utt，如果utt以test_list中某个为开头，则归为测试集，否则为训练集
    """
    train_out = open(train_path, "w")
    test_out = open(test_path, "w")

    for utt in utts:
        if is_start_in_list(utt, test_list):
            test_out.write(utt + "\n")
        else:
            train_out.write(utt + "\n")

    train_out.flush()
    train_out.close()

    test_out.flush()
    test_out.close()


def genscp_train_test_random(utts, train_path, test_path, test_num):
    """
    统计路径中的所有的utt，随机筛选出测试集和训练集，并在对应路径下生成 train.scp 和 test.scp
    """
    train_out = open(train_path, "w")
    test_out = open(test_path, "w")

    random.shuffle(utts)
    
    train_set = []
    test_set = []

    for index, utt in enumerate(utts):
        #if index > 10000:
        #     break
        if index < test_num:
            test_set.append(utt)
        else:
            train_set.append(utt)

    list2scp(test_set, test_path, sort=True)
    list2scp(train_set, train_path)


def genscp_from_file(file_path, out_path, sort=False):
    """
    统计文件中的所有的utt，写为scp文件 \n
    输入示例: \n
    000370	sil_S 我 记 得 你 的 手 机 就 是 v i v o 啊 sil_E	0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 \n
    000372	sil_S 啊 sil_E	0 0 0
    """
    data = open(file_path, 'r').readlines()
    filenames = [
        i.split('\t')[0].strip() for i in data
    ]
    
    if sort:
        filenames.sort()

    f = open(out_path, "w")
    f.write("\n".join(filenames))

    f.flush()
    f.close()


def genscp_from_file_train_test_by_start(file_path, train_path, test_path, test_list, sort=False):
    """
    统计文件中的所有的utt，如果utt以test_list中某个为开头，则归为测试集，否则为训练集 \n
    输入示例: \n
    000370	sil_S 我 记 得 你 的 手 机 就 是 v i v o 啊 sil_E	0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 \n
    000372	sil_S 啊 sil_E	0 0 0
    """
    data = open(file_path, 'r').readlines()
    train_out = open(train_path, "w")
    test_out = open(test_path, "w")

    filenames = [
        i.split('\t')[0].strip() for i in data
    ]

    if sort:
        filenames.sort()

    for filename in filenames:
        if is_start_in_list(filename, test_list):
            test_out.write(filename + "\n")
        else:
            train_out.write(filename + "\n")

    train_out.flush()
    train_out.close()

    test_out.flush()
    test_out.close()


def exclude_scp(ori_scp, ex_scp, sort=False):
    '''
    输入两个list, 返回差集
    '''
    out = list(set(ori_scp).difference(set(ex_scp)))
    if sort:
        out.sort()
    return out

def exclude_scp_2(ori_scp, ex_scp, sort=False):
    '''
    输入两个list, 使 ex 中每个 utt 都不是 ori 中任意 utt 的子字符串
    '''
    get = ori_scp
    for ex in ex_scp:
        tmp_get = []
        for g in get:
            if ex not in g:
                tmp_get.append(g)
        get = tmp_get
    if sort:
        get.sort()
    return get

def and_scp(scp_1, scp_2, sort=False):
    '''
    输入两个list, 返回交集
    '''
    out = list(set(scp_1).intersection(set(scp_2)))
    if sort:
        out.sort()
    return out


def gen_path_lst(path_list, postfix_list, utts, out_path, seq='|'):
    '''
    给定若干path，以及对应的postfix，生成path_list \n
    如: \n
    path1/utt1.postfix1|path2/utt1.postfix2\n
    path1/utt2.postfix1|path2/utt2.postfix2\n
    '''
    assert len(path_list) == len(postfix_list)
    line_list = []
    for utt in utts:
        info = []
        for index in range(len(path_list)):
            info.append(os.path.join(path_list[index], "{}.{}".format(utt, postfix_list[index])))
        line_list.append(seq.join(info))
    list2scp(line_list, out_path)


def genscp_by_ex(utts, RegExp, get_num=None):
    get = []
    for utt in utts:
        if re.search(RegExp, utt):
            get.append(utt)
    if get_num is not None:
        assert len(get) >= get_num, "except get {} but has {}".format(get_num, len(get))
        get = get[:get_num]
    return get


def split_scp_by_splitnum(utts, split_num, use_random=False):
    '''
    将传入的 utts 分割成 split_num 个 list，可选 random
    '''
    if use_random:
        random.shuffle(utts)
    
    each_num = math.ceil(1.0 * len(utts) / split_num)
    
    lst = [[] for i in range(split_num)]

    for index, utt in enumerate(utts):
        lst[math.floor(index/each_num)].append(utt)
        
    return lst


def split_scp_by_eachnum(utts, each_num, use_random=False):
    '''
    将传入的 utts 分割成若干个 list，每个 list 包含 each_num 个条目，可选 random
    '''
    if use_random:
        random.shuffle(utts)
    
    split_num = math.ceil(1.0 * len(utts) / each_num)
    
    lst = [[] for i in range(split_num)]

    for index, utt in enumerate(utts):
        lst[math.floor(index/each_num)].append(utt)
        
    return lst
    
    

def main():

    mode = 10
    
    if mode == 0:
        file_path = "/home/work_nfs5_ssd/hzli/data/testset/niren_test/niren_test_221023/labs_with_rest_speed_liandu_emph_emotion_modal"
        out_path = "/home/work_nfs5_ssd/hzli/data/testset/niren_test/niren_test_221023/file_lst/test.lst"
        genscp(file_path, out_path)
    elif mode == 1:
        file_path = "/home/work_nfs5_ssd/hzli/data/big_data/16k/mels/"
        out_path = "/home/work_nfs5_ssd/hzli/data/big_data/16k/file_lst/all.lst"
        genscp(file_path, out_path)
    elif mode == 2:
        utts = scp2list('/home/work_nfs5_ssd/hzli/data/niren/230210/file_lst/03/03_all.lst')
        out_path = "/home/work_nfs5_ssd/hzli/data/niren/230210/file_lst/tmp"
        genscp_divide_by_seq(utts, out_path, "out", 5)
    elif mode == 3:
        data_path = "/home/work_nfs5_ssd/hzli/data/big_data/file_lst/train.lst"
        out_path = "/home/work_nfs5_ssd/hzli/data/big_data/adapt/asr_syliu_4spk/file_lst"
        names = ["shannon_real_child_neutral", "shannon_neutral", "male_raw", "db_1_new"]
        genscp_divide_by_start_name(scp2list(data_path), out_path, names, write_all=True)
    elif mode == 4:
        utts = genscp_in_list("/home/work_nfs4_ssd/hzli/data/opencpop_new/acoustic_features_22k_hop256_win1024/mels")
        train_path = "/home/work_nfs4_ssd/hzli/data/opencpop_new/file_lst/train.lst"
        test_path = "/home/work_nfs4_ssd/hzli/data/opencpop_new/file_lst/test.lst"
        test_list = ["2044", "2086", "2092", "2093", "2100"]
        genscp_train_test_by_start(utts, train_path, test_path, test_list)
    elif mode == 5:
        base_dir = "/home/work_nfs5_ssd/hzli/data/big_data/16k"
        utts = scp2list(os.path.join(base_dir, 'file_lst/all_383spk_24wutt.lst'))
        train_path = os.path.join(base_dir, "file_lst", "train_383spk_24wutt.lst")
        test_path = os.path.join(base_dir, "file_lst", "test_383spk_24wutt.lst")
        test_num = 200
        genscp_train_test_random(utts, train_path, test_path, test_num)
    elif mode == 6:
        base_dir = "/home/work_nfs4_ssd/hzli/data/nlp/all_data_for-insert"
        utts = scp2list(os.path.join(base_dir, "file_lst", "path_v4.lst"))
        train_path = os.path.join(base_dir, "file_lst", "train.lst")
        test_path = os.path.join(base_dir, "file_lst", "test.lst")
        test_num = 2000
        genscp_train_test_random(utts, train_path, test_path, test_num)
    elif mode == 7:
        data_dir = "/home/work_nfs5_ssd/hzli/nlp/sequence_labeling/data/modal_predict/data_selected.txt"
        out_dir = "/home/work_nfs5_ssd/hzli/nlp/spontag-predictor_pro/data/corpus_3w/file_lst/selected.lst"
        genscp_from_file(data_dir, out_dir)
    elif mode == 8:
        data_dir = "/home/work_nfs5_ssd/hzli/nlp/sequence_labeling/data/tone_predict/data_selected.txt"
        train_path = "/home/work_nfs5_ssd/hzli/nlp/sequence_labeling/data/tone_predict/train.scp"
        test_path = "/home/work_nfs5_ssd/hzli/nlp/sequence_labeling/data/tone_predict/test.scp"
        test_list = ["000867", "001029", "001700", "000903", "000345", "000668", "000832", "000975", "000006", "000052", "001407", "001448"]
        genscp_from_file_train_test_by_start(data_dir, train_path, test_path, test_list)
    elif mode == 9:
        utts = scp2list("/home/work_nfs5_ssd/hzli/data/adapt/xielei/file_lst/135.lst")
        get = genscp_random(utts, 50)
        list2scp(get, "/home/work_nfs5_ssd/hzli/data/adapt/xielei/file_lst/135_50.lst")
    elif mode == 10:
        ori_scp = scp2list("/home/work_nfs4_ssd/ykli/data/vits/big_data/all2.lst")
        ex_scp = scp2list("/home/work_nfs5_ssd/hzli/kkcode/tmp/error.lst")
        out_dir = "/home/work_nfs5_ssd/hzli/kkcode/tmp/all2_durchecked.lst"
        out = exclude_scp(ori_scp, ex_scp)
        # out = exclude_scp(ex_scp, ori_scp)
        # print('\n'.join(out))
        # print(len(ori_scp))
        # print(len(out))
        list2scp(out, out_dir)
    elif mode == 11:
        utts = scp2list("/home/work_nfs5_ssd/hzli/data/niren/transfer/file_lst/targetspk_all.lst")
        print(len(utts))
        out_path = "/home/work_nfs5_ssd/hzli/data/niren/transfer/file_lst/targetspk_2m2f_50j.lst"
        starts2num = {
            "male_raw_":50,
            "db6_neutral_":50,
            "db_4_male_":50,
            "db_1_new":50
        }
        get = genscp_select_random_by_start(utts, starts2num)
        get.sort()
        list2scp(get, out_path)
    elif mode == 12:
        ori_scp = genscp_in_list("/home/work_nfs5_ssd/hzli/data/big_data/16k/durs_new")
        # list2scp(ori_scp, '/home/work_nfs5_ssd/hzli/kkcode/tmp/tmp.lst')
        # ex_scp = scp2list("/home/work_nfs5_ssd/hzli/data/big_data/16k/file_lst/train_383spk_24wutt.lst")
        out_dir = "/home/work_nfs5_ssd/hzli/data/big_data/16k/file_lst/test_383spk_24wutt_haslab_hasdur.lst"
        # out = exclude_scp_2(ori_scp, ex_scp)
        an = scp2list("/home/work_nfs5_ssd/hzli/data/big_data/16k/file_lst/test_383spk_24wutt_haslab.lst")
        out = and_scp(ori_scp, an)
        # print('\n'.join(out))
        print(len(an))
        print(len(out))
        list2scp(out, out_dir)
    elif mode == 13:
        scp1 = genscp_in_list("/home/work_nfs5_ssd/hzli/data/big_data/mels")
        scp2 = genscp_in_list("/home/work_nfs5_ssd/hzli/data/big_data/trimmed_wavs")
        out = and_scp(scp1, scp2)
        list2scp(out, "/home/work_nfs5_ssd/hzli/data/big_data/file_lst/mel.lst")
        print(len(scp1))
        print(len(scp2))
        print(len(out))    
    elif mode == 14:
        # 生成path list
        data_root = "/home/work_nfs4_ssd/hzli/data/biaobei_male_gta"
        path_list = [
            os.path.join(data_root, "mels"),
            os.path.join(data_root, "wavs"),
            os.path.join(data_root, "lf0")
        ]
        postfix_list = [
            "npy",
            "wav",
            "npy"
        ]
        gen_path_lst(path_list, postfix_list, genscp_in_list(os.path.join(data_root, "mels")), os.path.join(data_root, "all.lst"))
    elif mode == 15:
        utts = genscp_in_list("/home/backup_nfs4/data-TTS/jiuyuan/wavs")
        out_path = "/home/work_nfs5_ssd/hzli/kkcode/tmp/lst"
        os.makedirs(out_path, exist_ok=True)
        genscp_divide_by_start_auto(utts, out_path, auto_len=3)
    elif mode == 16:
        in_dir = "/home/work_nfs5_ssd/hzli/data/testset/emotion_test_aqy-emo/file_lst_all"
        out_dir = "/home/work_nfs5_ssd/hzli/data/testset/emotion_test_aqy-emo/file_lst"
        for file in os.listdir(in_dir):
            utts = scp2list(os.path.join(in_dir, file))
            get = genscp_random(utts, 100)
            list2scp(get, os.path.join(out_dir, file))
    elif mode == 17:
        utts_1 = genscp_in_list("/home/work_nfs5_ssd/hzli/data/niren/220924/durs")
        list2scp(utts_1, "/home/work_nfs5_ssd/hzli/data/niren/220924/file_lst/all_hasdur.lst")
        utts_2 = genscp_in_list("/home/work_nfs5_ssd/hzli/data/niren/220924/labs_with_rest_speed_liandu_emph_emotion_modal")
        utts_3 = scp2list("/home/work_nfs5_ssd/hzli/data/niren/220924/file_lst/all_morethan_1500.lst")
        utts_4 = scp2list("/home/work_nfs5_ssd/hzli/data/niren/220924/file_lst/all_pitch_cannot_interp1d.lst")
        utts = and_scp(utts_1, utts_2)
        utts = exclude_scp(utts, utts_3)
        utts = exclude_scp(utts, utts_4)
        all_path = "/home/work_nfs5_ssd/hzli/data/niren/220924/file_lst/all.lst"
        train_path = "/home/work_nfs5_ssd/hzli/data/niren/220924/file_lst/train.lst"
        test_path = "/home/work_nfs5_ssd/hzli/data/niren/220924/file_lst/test.lst"
        test_num = 16
        list2scp(utts, all_path)
        # genscp_train_test_random(utts, train_path, test_path, test_num)


if __name__ == "__main__":
    main()


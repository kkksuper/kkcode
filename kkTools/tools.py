import os
import sys
from tqdm import tqdm
import glob
import traceback
import re
import numpy as np
import pickle

def read_list_file(in_dir):
    '''
    读取 str(list) 保存的文件, list 每个元素为 str \n
    输入样例：\n
    ['2', '1', '岁', '的', '工']
    '''
    line = open(in_dir, 'r').readline().strip()[1:-1].split(',')
    items = [i.strip()[1:-1] for i in line]
    return items


def sort_1(x, y):
    """
    一种比较两个字符串的方法
    输入:
    2011_8.* 2011_11.*
    输出:
    先用下划线之前的数字转int比较，再用下划线后的数字转为int进行比较
    """
    x1 = int(x.split("_")[0])
    y1 = int(y.split("_")[0])
    x2 = int(x.split(".")[0].split("_")[1])
    y2 = int(y.split(".")[0].split("_")[1])

    if x1 == y1:
        return 1 if x2 > y2 else -1
    else:
        return 1 if x1 > y1 else -1


def sort_2(x, y):
    """
    一种比较两个字符串的方法
    输入:
    prefix_8.* prefix_11.*
    输出:
    用下划线后的数字转为int进行比较
    """
    x2 = int(x.split(".")[0].split("_")[1])
    y2 = int(y.split(".")[0].split("_")[1])

    return 1 if x2 > y2 else -1


def sort_3(x, y):
    """
    一种比较两个字符串的方法
    输入:
    ?8 ?11
    输出:
    去掉第一个字符后，转为数字为int后进行比较
    """
    x2 = int(x[1:])
    y2 = int(y[1:])

    return 1 if x2 > y2 else -1


def control_data_num_0(lst_1, lst_2, max_num):
    '''
    从 lst_1 中选取 max_num 个元素，且必须包含 lst_2 中含有的元素(如有)
    '''
    in2 = []
    not_in2 = []

    for utt in lst_1:
        if utt in lst_2:
            in2.append(utt)
        else:
            not_in2.append(utt)

    if len(in2) >= max_num:
        return in2[:max_num]
    else:
        in2.extend(not_in2[:max_num - len(in2)])
        return in2


def find_substr(str, substr):
    '''
    找到字符串中所有子字符串的start index (list)
    '''
    start_index = 0
    get_indexs = []

    while True:
        index = str[start_index:].find(substr)
        if index == -1:
            break
        else:
            real_index = index + start_index
            get_indexs.append(real_index)
            start_index = real_index + len(substr)
            if start_index >= len(str) - 1:
                break
    return get_indexs


def find_substr_onlyone(str, substr):
    '''
    找到字符串子字符串的 start index, 如果没有或者有多个，则返回 -1，否则返回 index
    '''
    index = str.find(substr)
    if index == -1:
        return -1
    else:
        if str[index + len(substr):].find(substr) != -1:
            return -1
        else:
            return index


def find_element_index_for_list(ob_list, word):
    return [i for (i, v) in enumerate(ob_list) if v == word]


def merge_pickle(files, outfile):
    '''
    读取多个 pickle，合并成一个，输入输出为文件路径
    '''
    data = {}
    for file in tqdm(files):
        d = pickle.load(open(file, 'rb'))
        data.update(d)
    pickle.dump(data, open(outfile, 'wb'))    


def main():

    mode = 7

    if mode == 0:
        print("some utils")
    elif mode == 1:
        print(sort_1("2044_8.lab", "2044_12.lab"))
    elif mode == 2:
        lst1 = [1, 2, 3, 4, 5, 6, 7]
        lst2 = [1, 3, 5, 199]
        out = control_data_num_0(lst1, lst2, 61)
        print(out)
    elif mode == 3:
        print(find_substr("123578121123", "123"))
    elif mode == 5:
        print(read_list_file("/home/work_nfs5_ssd/hzli/kkcode/tmp/tmp"))
    elif mode == 6:
        print(find_substr_onlyone("123578121123", "123"))
    elif mode == 7:
        base = '/home/work_nfs5_ssd/hzli/acoustic_model/evil/tmp'
        files = [os.path.join(base, f'vq2x32_out_{i}.pickle') for i in range(5)]
        outfile = '/home/work_nfs5_ssd/hzli/acoustic_model/evil/tmp/vq2x32.pickle'
        merge_pickle(files, outfile)


if __name__ == "__main__":
    main()

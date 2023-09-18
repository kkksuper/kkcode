from threading import enumerate
import os
import sys
import chardet
import numpy as np
import glob
import re
from tqdm import tqdm
from . import multiTask, scpTools, tools
import traceback
import json

# file encoding

def dedect_files_encoding(utts, in_dir):
    '''
    检测文件夹内文件编码
    '''
    coding = []
    for name in os.listdir(in_dir):
        if os.path.splitext(name)[0] in utts:
            coding.append(chardet.detect(open(os.path.join(in_dir, name)))["encoding"])
    coding = set(coding)
    return coding


def files_encodingConvert_from_to_by_encoding(input_path,
                                              output_path,
                                              encoding_old="UTF-16",
                                              encoding_new="utf-8"):
    """
    将输入路径下的所有 old 编码的文件转为 new 编码
    """

    if not os.path.isdir(output_path):
        os.mkdir(output_path)

    filenames = [os.path.basename(path) for path in os.listdir(input_path)]
    for filename in filenames:
        f = open(os.path.join(input_path, filename), mode="rb")
        data = f.read()
        print(filename + " encoding is: " + chardet.detect(data)["encoding"])

        if chardet.detect(data)["encoding"] == encoding_old:
            print("begin convert" + filename + " from " + encoding_old +
                  " to " + encoding_new)
            file_old = open(input_path + filename,
                            mode="r",
                            encoding=encoding_old)
            file_new = open(output_path + filename,
                            mode="w",
                            encoding=encoding_new)
            text = file_old.read()
            file_new.write(text)


def file_encodingConvert_to(input_path, output_path, encoding_new="utf-8"):
    """
    将输入文件转为 new 编码
    """

    f = open(input_path, mode="rb")
    data = f.read()
    # print(filename + " encoding is: " + chardet.detect(data)["encoding"])

    if chardet.detect(data)["encoding"] != encoding_new:
        # print("begin convert" + input_path + " from " +
        #       chardet.detect(data)["encoding"] + " to " + encoding_new)

        file_old = open(input_path,
                        mode="r",
                        encoding=chardet.detect(data)["encoding"])
        text = file_old.read()
        file_new = open(output_path, mode="w", encoding=encoding_new)
        file_new.write(text)


def files_encodingConvert_from_to_by_scp(args, scp):
    """
    将输入路径下的在scp中的所有文件转为 new 编码
    """

    input_path = args[0]
    output_path = args[1]
    encoding_new = "utf-8" if len(args) < 3 else args[2]

    if not os.path.isdir(output_path):
        os.mkdir(output_path)

    filenames = [
        os.path.basename(path) for path in os.listdir(input_path)
        if os.path.splitext(os.path.basename(path))[0] in scp
    ]
    for filename in tqdm(filenames):
        f = open(os.path.join(input_path, filename), mode="rb")
        data = f.read()
        # print(filename + " encoding is: " + chardet.detect(data)["encoding"])

        if chardet.detect(data)["encoding"] != encoding_new:
            '''
            print(
                "begin convert"
                + filename
                + " from "
                + chardet.detect(data)["encoding"]
                + " to "
                + encoding_new
            )
            '''
            try:
                file_old = open(input_path + filename,
                                mode="r",
                                encoding=chardet.detect(data)["encoding"])
                file_new = open(output_path + filename,
                                mode="w",
                                encoding=encoding_new)
                text = file_old.read()
                file_new.write(text)
            except Exception as e:
                print("error : {}, which encoding is {}".format(
                    filename,
                    chardet.detect(data)["encoding"]))
                traceback.print_exc()


# concat file


def concat_file(file1, file2, outpath):
    '''
    将文件1和文件2内容合并，输出至outpath
    '''
    f_1 = open(file1, "r").readlines()
    f_2 = open(file2, "r").readlines()
    f_out = open(outpath, "w")
    f_out.writelines(f_1)
    f_out.writelines('\n')
    f_out.writelines(f_2)
    f_out.flush()
    f_out.close()


def concat_files(file_list, outpath):
    '''
    将 file_list 中的所有文件内容合并，输出至outpath
    '''
    f_out = open(outpath, "w")
    for file in file_list:
        f = open(file, "r")
        tmp = f.readlines()
        if tmp[-1].endswith('\n'):
            f_out.writelines(tmp)
        else:
            f_out.writelines(tmp)
            f_out.write('\n')
        f.flush()
        f.close()
    f_out.flush()
    f_out.close()


def search_by_ex_in_line(file_in, RegExp):
    '''
    根据正则表达式查找文件中的内容，并返回查找到的每一行
    '''
    f = open(file_in, 'r')
    find_lines = []

    for line in f.readlines():
        if re.search(RegExp, line):
            find_lines.append((line))

    return find_lines


def sort_by_line(in_dir, out_dir):
    '''
    读取文件的每一行. 按照字符串进行排序后, 输出
    '''
    if not os.path.isfile(in_dir):
        print(in_dir + " is not a file")
        exit(0)

    old = open(in_dir, 'r').readlines()
    old.sort()
    new = open(out_dir, 'w')
    new.writelines(old)

    new.flush()
    new.close()


def unzip_file(utt, in_dir, out_dir):
    '''
    解压 zip 文件到 out_dir 下
    '''
    shell = f"unzip -d {out_dir} {os.path.join(in_dir, f'{utt}.zip')}"
    print(shell)
    os.system(shell)


def replace_file_content(in_path, old_content, replace_content):
    '''
    根据正则表达式，将文件中所有对应的内容替换为新内容
    '''
    f = open(in_path,'r')
    lines = f.readlines()
    f.close()
    f = open(in_path,'w+')
    for line in lines:
        new_line = re.sub(old_content, replace_content, line)
        f.writelines(new_line)
    f.close()


def main():

    mode = 8

    if mode == 0:
        return "some file utils"
    elif mode == 1:
        dir1 = "/home/work_nfs5_ssd/hzli/data/db6_neutral/clean_labels/"
        dir2 = "/home/work_nfs5_ssd/hzli/data/db6_neutral/labs_utf8/"
        scp = "/home/work_nfs5_ssd/hzli/kkcode/encoding_error.scp"
        files_encodingConvert_from_to_by_scp([dir1, dir2],
                                             scpTools.scp2list(scp))
    elif mode == 2:
        dir1 = "/home/work_nfs5_ssd/hzli/data/adapt/aslp_10j-db6_1k-db4_1k/utt2spk"
        dir2 = "/home/work_nfs5_ssd/hzli/data/adapt/aslp10j/utt2spk"
        out_dir = "/home/work_nfs5_ssd/hzli/data/adapt/aslp_10j-db6_1k-db4_1k/utt2spk"
        concat_file(dir1, dir2, out_dir)
    elif mode == 3:
        file_in = "/home/work_nfs5_ssd/hzli/nlp/sequence_labeling/data/modal_predict/origin_data.txt"
        RegExp = "[a-zA-Z]+"
        out = search_by_ex_in_line(file_in, RegExp)
        ids = [i.strip().split('\t')[0] for i in out]
        print('\n'.join(ids))
    elif mode == 4:
        in_dir = "/home/work_nfs4_ssd/hzli/nlp/sequence_labeling/egs/polyphone_predict_txt_blstm_mergedata/tmp.log"
        out_dir = "/home/work_nfs4_ssd/hzli/nlp/sequence_labeling/egs/polyphone_predict_txt_blstm_mergedata/tmp_sort.log"
        sort_by_line(in_dir, out_dir)
    elif mode == 5:
        file_lst = glob.glob(
            "/home/work_nfs5_ssd/hzli/data/biaobei/220924/tmp/trim_info/*.txt")
        outpath = "/home/work_nfs5_ssd/hzli/data/biaobei/220924/trim_info.txt"
        concat_files(file_lst, outpath)
    elif mode == 6:
        file_encodingConvert_to(
            "/home/work_nfs4_ssd/hzli/data/duoyinzi/dataset_biaobei/back_letter2pronun.json",
            "/home/work_nfs4_ssd/hzli/data/duoyinzi/dataset_biaobei/back_letter2pronun_utf8.json"
        )
    elif mode == 7:
        in_dir = "/home/backup_nfs4/data-TTS/hzli/1/origin_data/"
        out_dir = "/home/backup_nfs4/data-TTS/hzli/1"
        utts = glob.glob(in_dir + "/*.zip")
        utts = [os.path.splitext(os.path.basename(i))[0] for i in utts]
        for utt in tqdm(utts):
            unzip_file(utt, in_dir, os.path.join(out_dir, utt))
    elif mode == 8:
        replace_file_content("/home/work_nfs5_ssd/hzli/kkcode/workroom/20220924-biaobei/__pycache__/123.txt", "5\.691375", "123")

if __name__ == "__main__":
    main()

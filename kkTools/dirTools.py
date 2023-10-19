import os
import shutil
import sys
from tqdm import tqdm
import glob
import traceback
import re
import functools
from . import tools, scpTools


def compareDir_by_format(dir_1, dir_2, format_1, format_2):
    '''
    比较路径1存在而路径2不存在的文件，返回差异列表与总数，目录均需以"/"结尾 \n
    查看dir1下的 format1 格式文件，是否在dir2中存在同名的 format2 格式文件（如 .lab .wav）
    '''
    assert os.path.isdir(dir_1) and os.path.isdir(
        dir_2), "error path, please check: " + dir_1 + " and " + dir_2

    list1 = glob.glob(dir_1 + "*" + format_1)
    list2 = glob.glob(dir_2 + "*" + format_2)

    list1 = [os.path.splitext(os.path.basename(path))[0] for path in list1]
    list2 = [os.path.splitext(os.path.basename(path))[0] for path in list2]

    tmp = list(set(list1).difference(set(list2)))
    tmp.sort()
    return tmp


def compareDir_after_start(dir_1, dir_2, name):
    '''
    首先筛选出两个文件夹内所有以name为开头的文件，然后比较路径1存在而路径2不存在的文件，返回差异列表与总数，目录均需以"/"结尾 \n
    只比较名字，忽略格式
    '''
    assert os.path.isdir(dir_1) and os.path.isdir(
        dir_2), "error path, please check: " + dir_1 + " and " + dir_2

    list1 = [
        os.path.splitext(os.path.basename(path))[0]
        for path in os.listdir(dir_1)
        if os.path.splitext(os.path.basename(path))[0].startswith(name)
    ]
    list2 = [
        os.path.splitext(os.path.basename(path))[0]
        for path in os.listdir(dir_2)
        if os.path.splitext(os.path.basename(path))[0].startswith(name)
    ]

    tmp = list(set(list1).difference(set(list2)))
    tmp.sort()
    return tmp


def compareDir_by_name(dir_1, dir_2):
    '''
    比较路径1存在而路径2不存在的文件，返回name list，目录均需以"/"结尾 \n
    只比较名字，忽略格式
    '''
    assert os.path.isdir(dir_1) and os.path.isdir(
        dir_2), "error path, please check: " + dir_1 + " and " + dir_2

    list1 = [
        os.path.splitext(os.path.basename(path))[0]
        for path in os.listdir(dir_1)
    ]
    list2 = [
        os.path.splitext(os.path.basename(path))[0]
        for path in os.listdir(dir_2)
    ]

    tmp = list(set(list1).difference(set(list2)))
    tmp.sort()
    return tmp


def compareDir_concat(dir_1, dir_2):
    '''
    比较路径1存在而路径2不存在的文件，返回name list，dir1 需以"/"结尾, dir2 不需要(可以加一些前缀) \n
    '''
    file_names = os.listdir(dir_1)
    file_names.sort()

    file_list = []

    for index in range(len(file_names)):

        file_name = os.path.split(file_names[index])[0]

        if not os.path.isfile(dir_2 + file_name):
            file_list.append(file_name)

    return file_list


def get_same_by_name(dir_1, dir_2):
    '''
    比较路径1和路径2均存在的文件，返回name list，目录均需以"/"结尾 \n
    只比较名字，忽略格式
    '''
    assert os.path.isdir(dir_1) and os.path.isdir(
        dir_2), "error path, please check: " + dir_1 + " and " + dir_2

    list1 = [
        os.path.splitext(os.path.basename(path))[0]
        for path in os.listdir(dir_1)
    ]
    list2 = [
        os.path.splitext(os.path.basename(path))[0]
        for path in os.listdir(dir_2)
    ]

    tmp = list(set(list1).intersection(set(list2)))
    tmp.sort()
    return tmp


def get_all_dir(rootDir):
    '''
    返回路径下所有文件夹的name list
    '''
    return [
        i for i in os.listdir(rootDir)
        if os.path.isdir(os.path.join(rootDir, i) + "/")
    ]

def get_all_dir_r(rootDir):
    '''
    返回路径下所有文件夹对应的路径 list
    '''
    get_dirs = []
    if not os.path.isdir(rootDir):
        return get_dirs
    files = os.listdir(rootDir)
    for file in files:
        cur_path = os.path.join(rootDir, file)
        if os.path.isdir(cur_path):
            get_dirs.append(cur_path)
            new_dirs = get_all_dir_r(cur_path)
            get_dirs.extend(new_dirs)
    return get_dirs


def del_all_dir(rootDir):
    '''
    删除路径下所有文件夹
    '''
    dirs = [
        os.path.join(rootDir, i) for i in os.listdir(rootDir)
        if os.path.isdir(os.path.join(rootDir, i) + "/")
    ]
    for i in dirs:
        os.system("rm -rf " + i)
    return dirs


def ln_files_by_scp(in_dir, out_dir, utts=None, prefix=""):
    '''
    根据scp(list)，将某文件夹所有文件名符合的文件链接到另一个文件夹
    '''
    if not os.path.isdir(out_dir):
        os.mkdir(out_dir)
    
    if utts is None:
        utts = scpTools.genscp_in_list(in_dir)

    files = os.listdir(in_dir)
    files.sort()
    for file in tqdm(files):
        if os.path.splitext(file)[0] in utts:
            try:
                # print("ln -s " + dir_1 + file + " " + dir_2 + file)
                os.system("ln -s " + os.path.join(in_dir, file) + " " +
                          os.path.join(out_dir, prefix + file))
                # print("ln -s " + os.path.join(in_dir, file) + " " + os.path.join(out_dir, os.path.splitext(file)[0] + "_gta" + os.path.splitext(file)[1]))
                # os.system("ln -s " + os.path.join(in_dir, file) + " " + os.path.join(out_dir, os.path.splitext(file)[0] + "_gta" + os.path.splitext(file)[1]))
            except Exception as e:
                if "no such" in str(e).lower():
                    print("no such file: ", os.path.join(in_dir, file))
                    traceback.print_exc()
                    continue
                else:
                    traceback.print_exc()
                    break

def ln_files_by_scp_with_format(in_dir, out_dir, utts, target_format='wav', prefix=""):
    '''
    根据scp(list)，将某文件夹所有文件名符合的文件链接到另一个文件夹
    '''
    if not os.path.isdir(out_dir):
        os.mkdir(out_dir)\
        
    for utt in tqdm(utts):
        infile = os.path.join(in_dir, f"{utt}.{target_format}")
        outfile = os.path.join(out_dir, prefix + f"{utt}.{target_format}")
        try:
            if os.path.isfile(infile):
                # print("ln -s " + dir_1 + file + " " + dir_2 + file)
                os.system("ln -s " + infile + " " +
                            outfile)
                # print("ln -s " + os.path.join(in_dir, file) + " " + os.path.join(out_dir, os.path.splitext(file)[0] + "_gta" + os.path.splitext(file)[1]))
                # os.system("ln -s " + os.path.join(in_dir, file) + " " + os.path.join(out_dir, os.path.splitext(file)[0] + "_gta" + os.path.splitext(file)[1]))
            else:
                print(f'warning: no such file in source dictory: {infile}')
        except Exception as e:
            if "no such" in str(e).lower():
                print("no such file: ", os.path.join(in_dir, file))
                traceback.print_exc()
                continue
            else:
                traceback.print_exc()
                break        

def cp_dir(in_dir, out_dir, readlink=False):
    '''
    把一个文件夹复制一份，并保持目录结构不变。
    可替换里面的软链为实际文件（可选）
    '''
    os.makedirs(out_dir, exist_ok=True)

    # 遍历源文件夹中的所有文件和文件夹
    for item in os.listdir(in_dir):
        item_path = os.path.join(in_dir, item)
        destination_path = os.path.join(out_dir, item)

        if os.path.islink(item_path) and readlink:
            # 如果是软链文件，则替换为实际文件
            target_path = os.path.realpath(item_path)
            shutil.copy2(target_path, destination_path)
        elif os.path.isdir(item_path):
            # 如果是文件夹，则递归复制文件夹
            cp_dir(item_path, destination_path, readlink)
        else:
            # 如果是普通文件，则直接复制
            shutil.copy2(item_path, destination_path)
            

def cp_files_by_utts(dir_1, dir_2, utts, prefix=""):
    '''
    根据scp(list)，复制某文件夹所有文件名符合的文件到另一个文件夹
    '''
    if not os.path.isdir(dir_2):
        os.mkdir(dir_2)

    utts = [prefix + i for i in utts]

    files = os.listdir(dir_1)
    num = 0
    for file in tqdm(files):
        if os.path.splitext(file)[0] in utts:
            try:
                # print("cp " + dir_1 + file + " " + dir_2 + file)
                os.system("cp " + os.path.join(dir_1, file) + " " +
                          os.path.join(dir_2, file))
                num += 1
            except Exception as e:
                if "no such" in str(e).lower():
                    print("no such file: ", os.path.join(dir_1, file))
                    traceback.print_exc()
                    continue
                else:
                    traceback.print_exc()
                    break
    print("already cp {} files, need {} files".format(num, len(utts)))


def cp_files_by_name(dir_1, dir_2, names, prefix=""):
    '''
    根据scp(list)，复制某文件夹所有文件名符合的文件到另一个文件夹
    '''
    if not os.path.isdir(dir_2):
        os.mkdir(dir_2)

    names = [prefix + i for i in names]

    files = os.listdir(dir_1)
    num = 0
    for file in tqdm(files):
        if file in names:
            try:
                # print("cp " + dir_1 + file + " " + dir_2 + file)
                os.system("cp " + os.path.join(dir_1, file) + " " +
                          os.path.join(dir_2, file))
                num += 1
            except Exception as e:
                if "no such" in str(e).lower():
                    print("no such file: ", os.path.join(dir_1, file))
                    traceback.print_exc()
                    continue
                else:
                    traceback.print_exc()
                    break
    print("already cp {} files, need {} files".format(num, len(names)))


def cp_files_by_ex(dir_1, dir_2, RegExp):
    '''
    根据正则表达式，复制某文件夹所有文件名符合的文件到另一个文件夹
    '''
    if not os.path.isdir(dir_2):
        os.mkdir(dir_2)

    files = os.listdir(dir_1)
    files.sort()
    for file in tqdm(files):
        if re.search(RegExp, file):
            # print("cp " + dir_1 + file + " " + dir_2 + file)
            os.system("cp " + os.path.join(dir_1, file) + " " +
                      os.path.join(dir_2, file))


def cp_files_by_replace(dir_1, dir_2, oldstr, newstr):
    '''
    把dir_1下所有的文件复制到dir_2，并将文件名中的 oldstr 替换为 newstr
    '''
    if not os.path.isdir(dir_2):
        os.mkdir(dir_2)

    files = os.listdir(dir_1)
    files.sort()
    for file in tqdm(files):
        new_file = file.replace(oldstr, newstr)
        print("cp " + os.path.join(dir_1, file) + " " +
              os.path.join(dir_2, new_file))
        os.system("cp " + os.path.join(dir_1, file) + " " +
                  os.path.join(dir_2, new_file))


def cp_files_by_scp_with_format(in_dir, out_dir, utts, target_format='wav', prefix=""):
    '''
    根据scp(list)，将某文件夹所有文件名符合的文件复制到另一个文件夹
    '''
    if not os.path.isdir(out_dir):
        os.mkdir(out_dir)\
        
    for utt in tqdm(utts):
        infile = os.path.join(in_dir, f"{utt}.{target_format}")
        outfile = os.path.join(out_dir, prefix + f"{utt}.{target_format}")
        try:
            if os.path.isfile(infile):
                os.system("cp " + infile + " " +
                            outfile)
            else:
                print(f'warning: no such file in source dictory: {infile}')
        except Exception as e:
            if "no such" in str(e).lower():
                print("no such file: ", os.path.join(in_dir, file))
                traceback.print_exc()
                continue
            else:
                traceback.print_exc()
                break  


def mv_files_by_replace(dir_1, dir_2, oldstr, newstr):
    '''
    把dir_1下所有的文件移动到dir_2，并将文件名中的 oldstr 替换为 newstr
    '''
    if not os.path.isdir(dir_2):
        os.mkdir(dir_2)

    files = os.listdir(dir_1)
    files.sort()
    for file in tqdm(files):
        new_file = file.replace(oldstr, newstr)
        if dir_1 == dir_2 and file == new_file:
            continue
        print("mv " + os.path.join(dir_1, file) + " " +
              os.path.join(dir_2, new_file))
        os.system("mv " + os.path.join(dir_1, file) + " " +
                  os.path.join(dir_2, new_file))


def mv_files_by_scp(dir_1, dir_2, scp):
    '''
    根据scp(list)，移动某文件夹所有文件名符合的文件到另一个文件夹
    '''
    if not os.path.isdir(dir_2):
        os.mkdir(dir_2)

    files = os.listdir(dir_1)
    files.sort()
    for file in tqdm(files):
        if os.path.splitext(file)[0] in scp:
            # print("mv " + os.path.join(dir_1, file) + " " + os.path.join(dir_2, file))
            os.system("mv " + os.path.join(dir_1, file) + " " +
                      os.path.join(dir_2, file))


def rm_file_by_name(dir, scp):
    '''
    删除路径下，文件名在scp(list)中的所有文件
    '''
    file_names = glob.glob(dir + "/*")
    file_names.sort()
    num = 0

    for index in tqdm(range(len(file_names))):
        file_name = os.path.splitext(os.path.basename(file_names[index]))[0]
        # print(file_name)
        if file_name in scp:
            os.system("rm " + file_names[index])
            num += 1

    print("del num: ", num)
    return num


def rm_file_by_end(dir, end):
    '''
    删除路径下，文件名以end结尾的所有文件
    '''
    file_names = glob.glob(dir + "/*")
    file_names.sort()
    num = 0

    for index in tqdm(range(len(file_names))):
        file_name = os.path.basename(file_names[index])
        if file_name.endswith(end):
            print("rm {}".format(file_names[index]))
            os.system("rm " + file_names[index])
            num += 1

    print("del num: ", num)
    return num


def rename_file_in_num(in_dir, add_num):
    '''
    更改文件名，将其中的数字加上 add_num \n
    文件名格式: prefix_num.format
    '''
    utts = os.listdir(in_dir)
    utts.sort(key=functools.cmp_to_key(tools.sort_2))

    for utt in utts:
        if not utt.startswith("ycy"):
            continue
        name = os.path.splitext(utt)[0]
        postfix = utt.split('.')[1]
        prefix = name.split('_')[0]
        index = int(name.split("_")[1])
        if index < 46:
            continue
        print("mv " + os.path.join(in_dir, utt) + " " +
              os.path.join(in_dir, prefix + "_" + str(index + add_num) + "." +
                           postfix))
        os.system("mv " + os.path.join(in_dir, utt) + " " + os.path.join(
            in_dir, prefix + "_" + str(index + add_num) + "." + postfix))


def gatherFile(rootDir, out_dir, deep=6, seq=''):
    '''
    将多级目录的所有文件，汇聚到另一个目录中（一级目录），删去的路径信息用seq拼接在新文件名开头 \n
    具体规则: \n
    第deep层及之后的路径用seq作为分割符加入到文件名中，并将文件输出到指定路径 \n
    样例: \n
    输入 /home/work_nfs5_ssd/hzli/data/_24k_labels/db_1_cn_raw_/000001.lab /home/work_nfs5_ssd/hzli/data/24k_labels/ 6 '' \n
    输出 /home/work_nfs5_ssd/hzli/data/24k_labels/db_1_cn_raw_000001.lab \n
    '''
    if not os.path.isdir(rootDir):
        print("this seem is not a dir: " + rootDir)
        return
    print("deal with dir:" + rootDir)
    files = os.listdir(rootDir)
    num = 0
    for file in files:
        try:
            cur_path = os.path.join(rootDir, file)
            if os.path.isdir(cur_path):
                print("go to dir:" + cur_path)
                gatherFile(cur_path, out_dir, deep, seq)
            else:
                newName = os.path.join(out_dir,
                                       seq.join(cur_path.split('/')[deep:]))
                # newName = os.path.join(out_dir, seq.join(cur_path.split('/')[deep: deep + 2]) + "_" + os.path.basename(cur_path))
                if not os.path.isfile(newName):
                    # print(cur_path)
                    num += 1
                    print("cp " + cur_path + " " + newName)
                    os.system("cp " + cur_path + " " + newName)
        except Exception as e:
            print("error file: " + file)
            traceback.print_exc()
            continue
    if num != 0:
        print("total num in " + rootDir + " is: " + str(num))


def gatherFile_v2(rootDir,
                  out_dir,
                  operation="mv",
                  prefix="",
                  seq='_',
                  exclude_dirs=[],
                  exclude_files=[],
                  deep=0,
                  maxdeep=None,
                  has_prefix=True):
    '''
    将多级目录的所有文件，汇聚到另一个目录中,并用中间的路径名作为最终的文件名前缀(可选) \n
    返回得到的文件数
    '''
    if not os.path.isdir(rootDir):
        print("this seem is not a dir: " + rootDir)
        return
    os.makedirs(out_dir, exist_ok=True)

    print("deal with dir:" + rootDir)
    files = os.listdir(rootDir)
    num = 0
    for file in files:
        try:
            cur_path = os.path.join(rootDir, file)
            if os.path.isdir(cur_path):
                if file in exclude_dirs or (maxdeep is not None
                                            and deep + 1 > maxdeep):
                    continue
                print("go to dir:" + cur_path)
                if has_prefix or prefix == '':
                    num += gatherFile_v2(cur_path, out_dir, operation, file,
                                         seq, exclude_dirs, exclude_files,
                                         deep + 1, maxdeep, has_prefix)
                else:
                    num += gatherFile_v2(cur_path, out_dir, operation,
                                         prefix + seq + file, seq,
                                         exclude_dirs, exclude_files, deep + 1,
                                         maxdeep, has_prefix)
            else:
                if has_prefix or prefix == '':
                    newName = os.path.join(out_dir, prefix + seq + file)
                else:
                    newName = os.path.join(out_dir, file)
                if not os.path.isfile(newName) and not os.path.splitext(
                        file)[0] in exclude_files:
                    num += 1
                    # print(f"{operation} {cur_path} {newName}")
                    os.system(f"{operation} {cur_path} {newName}")
        except Exception as e:
            print("error file: " + file)
            traceback.print_exc()
            continue
    return num


def gatherDir(rootDir,
              out_dir,
              operation="mv",
              prefix="",
              seq='_',
              target_dirs=[],
              include_dirs=[],
              deep=0,
              maxdeep=None):
    '''
    将多级目录的所有文件，汇聚到另一个目录中,并用中间的路径名作为最终的文件名前缀 \n
    返回得到的文件数
    '''
    if not os.path.isdir(rootDir):
        print("this seem is not a dir: " + rootDir)
        return
    # print("deal with dir:" + rootDir)
    files = os.listdir(rootDir)
    num = 0
    for file in files:
        try:
            cur_path = os.path.join(rootDir, file)
            if os.path.isdir(cur_path):
                isop = False

                for target_dir in target_dirs:
                    if target_dir in file:
                        num += 1
                        isop = True
                        newName = os.path.join(
                            out_dir, prefix + seq +
                            file) if prefix != '' else os.path.join(
                                out_dir, file)
                        print(prefix, newName)
                        print(f"{operation} {cur_path} {newName}")
                        os.system(f"{operation} {cur_path} {newName}")
                        break

                if isop or (maxdeep is not None and deep + 1 > maxdeep):
                    continue

                if len(include_dirs) == 0:
                    # print("go to dir:" + cur_path)
                    num += gatherDir(cur_path, out_dir, operation,
                                     prefix + seq + file, seq, target_dirs,
                                     include_dirs, deep + 1, maxdeep)
                else:
                    for include_dir in include_dirs:
                        if include_dir in file:
                            # print("go to dir:" + cur_path)
                            num += gatherDir(cur_path, out_dir, operation,
                                             prefix + seq + file, seq,
                                             target_dirs, include_dir,
                                             deep + 1, maxdeep)
                            break
        except Exception as e:
            print("error file: " + file)
            traceback.print_exc()
            continue
    return num


def plot_dir_struct(root_dir, depth=0, show_file=False, exclude_file_postfix=[".wav", ".interval"], exclude_dir_subname=['.git'], sub_char = '| '):
    '''
    用字符串的形式画出 root_dir 下所有文件夹的结构，忽略文件
    '''
    if depth == 0:
        print("root:[" + root_dir + "]")

    names = os.listdir(root_dir)
    names.sort()
    for name in names:

        thisitem = root_dir + '/' + name

        # exclude check and print tree
        if os.path.isfile(thisitem):
            
            # exclude all file if is_include_file is False
            if not show_file:
                continue

            # exclude file which name endswith exclude_file_postfix
            ex = [name.endswith(ex) for ex in exclude_file_postfix]
            if len(set(ex)) != 1:
                continue

            # print tree
            linkinfo = " --> " + os.readlink(thisitem) if os.path.islink(thisitem) else ""
            print(sub_char * depth + "+--" + name + " " +
                linkinfo)
        else:
            # exclude dir which exclude_dir_subname in name
            ex = [ex in name for ex in exclude_dir_subname]
            if len(set(ex)) != 1:
                continue
        
            # print ilnk
            linkinfo = " --> " + os.readlink(thisitem) if os.path.islink(thisitem) else ""
            print(sub_char * depth + "+--" + name + " " +
                str(len(os.listdir(thisitem))) + 
                linkinfo)
            
            # next depth
            plot_dir_struct(thisitem, depth + 1, show_file, exclude_file_postfix, exclude_dir_subname, sub_char)
            


def main():

    mode = 0

    if mode == 0:
        for ex in ['F0312.*', 'F03-M83-03.*', 'F03-M84-03']:
            dir_1 = "/home/work_nfs5_ssd/hzli/data/niren/230210/linguistic_feature/txts"
            out_dir = "/home/work_nfs6/hzli/third_party/AcademiCodec/egs/HiFi-Codec-24k-320d/txts"
            cp_files_by_ex(dir_1, out_dir, ex)
    elif mode == 1:
        dir1 = "/home/work_nfs5_ssd/hzli/data/biaobei/base/wavs/"
        dir2 = "/home/work_nfs5_ssd/hzli/data/biaobei/base/txts/"
        out = compareDir_by_name(dir1, dir2)
        # scpTools.list2scp(out, "del.scp")
        print('\n'.join(out))
    elif mode == 2:
        dir = "/home/work_nfs5_ssd/hzli/data/genshin/processed_data/labs/"
        scp = "/home/work_nfs5_ssd/hzli/data/genshin/processed_data/file_lst/tmp_1.lst"
        rm_file_by_name(dir, scpTools.scp2list(scp))
    elif mode == 3:
        for name in ['2044', '2086', '2092', '2093', '2100']:
            dir_1 = "/home/work_nfs5_ssd/hzli/data/db6_neutral/clean_labels/"
            out_dir = "/home/work_nfs5_ssd/hzli/data/db6_neutral/labs_utf8/"
            print('\n'.join(compareDir_after_start(dir_1, out_dir, name)))
    elif mode == 4:
        dir_1 = "/home/work_nfs6/hzli/logdir/db6_24k_emo_control/db6_24k_emo_control_20220919_nobn/40w_testforaqy-emo_scale"
        out_dir = "/home/work_nfs6/hzli/logdir/db6_24k_emo_control/db6_24k_emo_control_20220919_nobn/40w_testforaqy-emo_scale_gather"
        os.makedirs(out_dir, exist_ok=True)
        '''
        for x in tqdm(os.listdir(dir_1)):
            gatherFile(os.path.join(dir_1, x.strip()), out_dir)
        '''
        gatherFile(dir_1, out_dir, deep=8, seq='_')
    elif mode == 5:
        dir1 = "/home/work_nfs5_ssd/hzli/logdir/multi_fs2_220217_pitch_norm/100w_wav/syn_mix_6"
        end = "npy"
        rm_file_by_end(dir1, end)
    elif mode == 6:
        dir1 = "/home/work_nfs5_ssd/hzli/data/db6/wavs/"
        dir2 = "/home/work_nfs5_ssd/hzli/data/db6/labs/"
        print('\n'.join(get_same_by_name(dir1, dir2)))
    elif mode == 7:
        dir_1 = "/home/work_nfs5_ssd/hzli/data/db6/durs_kaldi"
        oldstr = "db6_neural"
        newstr = "db6_neutral"
        mv_files_by_replace(dir_1, dir_1, oldstr, newstr)
    elif mode == 8:
        in_dir = "/home/work_nfs5_ssd/hzli/data/niren/230210/linguistic_feature/labs_with_fp_rest_speed_liandu_emph_emotion_modal"
        out_dir = "/home/work_nfs5_ssd/hzli/data/niren/transfer/labs_events_fp"
        utts = scpTools.genscp_in_list(
            in_dir
        )
        ln_files_by_scp_with_format(in_dir, out_dir, utts, 'lab')
    elif mode == 9:
        dir_1 = "/home/work_nfs4_ssd/hzli/data/nlp/all_data/syllabel_labels_nosil_hastag/"
        dir_2 = "/home/work_nfs4_ssd/hzli/data/nlp/all_data/txts/"
        format_1 = ".lab"
        format_2 = ".txt"
        out = compareDir_by_format(dir_1, dir_2, format_1, format_2)
        print('\n'.join(out))
    elif mode == 10:
        dir_1 = "/home/work_nfs5_ssd/hzli/data/niren/230210/durs/durs_htk_trim15_transfer_16k200_delfp"
        dir_2 = "/home/work_nfs5_ssd/hzli/data/niren/transfer/durs_delfp"
        
        utts = scpTools.genscp_in_list(dir_1)
        cp_files_by_utts(dir_1, dir_2, utts)
    elif mode == 11:
        dir_1 = "/home/work_nfs6/hzli/logdir/adapt_24k/vctk_3spk/1w"
        out_dir = "/home/work_nfs6/hzli/logdir/adapt_24k/vctk_3spk/1w_mels"
        os.makedirs(out_dir, exist_ok=True)
        '''
        for x in tqdm(os.listdir(dir_1)):
            gatherFile(os.path.join(dir_1, x.strip()), out_dir)
        '''
        gatherFile(dir_1, out_dir, deep=8, seq='_')
    elif mode == 12:
        in_dir = "/home/work_nfs5_ssd/hzli/data/didi_audition4spk/new_wavs"
        add_num = -1
        rename_file_in_num(in_dir, add_num)
    elif mode == 13:
        root_dir = "/home/backup_nfs4/ymzhang/data/huawei_38"
        plot_dir_struct(root_dir, depth=2, show_file=True, sub_char='\t')
    elif mode == 14:
        in_dir = "/home/work_nfs6/hzli/logdir/niren"
        out_dir = "/home/work_nfs6/hzli/logdir/niren_laugh/20221119_gather_laugh"
        target_dirs = ['laugh']
        gatherDir(in_dir, out_dir, operation='mv', target_dirs=target_dirs)
    elif mode == 15:
        dir_1 = "/home/work_nfs5_ssd/hzli/kkcode/tmp/course/yunchouxue/运筹学课件"
        out_dir = "/home/work_nfs5_ssd/hzli/kkcode/tmp/course/yunchouxue/ppt"
        os.makedirs(out_dir, exist_ok=True)
        gatherFile_v2(dir_1, out_dir, operation='cp', has_prefix=False, exclude_files=['前言', '绪论', '复习题'])
    elif mode == 16:
        cp_dir('/home/work_nfs5_ssd/hzli/kkcode/workroom/20230907-spontts_icassp/SponTTS/subjective', 
               '/home/work_nfs5_ssd/hzli/kkcode/workroom/20230907-spontts_icassp/SponTTS/subjective_readlink', 
               readlink=True)


if __name__ == "__main__":
    main()

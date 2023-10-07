import os
from tqdm import tqdm
import json
import re
import random
from . import tools, spkTools, jsonTools, scpTools, labelTools

def gen_dict(in_dir, out_dir):
    '''
    读取一个文件内的所有字符，构建一个字符集
    '''
    assert os.path.isfile(in_dir), "{} seem not a file".format(in_dir)
    letter_list = []
    f_in = open(in_dir, 'r')
    f_out = open(out_dir, 'w')
    for line in tqdm(f_in.readlines()):
        for letter in line.strip():
            if letter not in letter_list:
                letter_list.append(letter)

    print("dict len: {}".format(len(letter_list)))

    f_out.write(str(letter_list))
    f_out.flush()
    f_out.close()

    print("complete!")

def judge_is_modal_insert(text):
    '''
    输入一段字符串，判断是否有语气词，以及是否有开头语气词
    '''
    modals=["嗯", "呃", "就是", "那个"]
    for modal in modals:
        find_i = text.find(modal)
        if find_i != -1:
            has_modal = True
            if find_i == 0:
                has_start_modal = True
    return has_modal, has_start_modal


def judge_has_repeat(text, limit_repeat_words=None):
    '''
    输入一段字符串, 判断是否有重复字词(词长最多为2) \n
    返回重复的字词 list，以及是否开头有重复字 \n
    如果 limit_repeat_words 不为空，则只查找其中的重复字词
    '''
    repeat = []
    has_start_repeat = False
    for index in range(len(text)):
        if index > 0 and text[index] == text[index-1] and not text[index] in repeat:
            find = text[index]
            if limit_repeat_words is None or (limit_repeat_words is not None and find in limit_repeat_words):
                repeat.append(find)
                if index == 1:
                    has_start_repeat = True
        if index > 2 and text[index-1] + text[index] == text[index-3] + text[index-2] and not text[index-1] + text[index] in repeat:
            find = text[index-1] + text[index]
            if limit_repeat_words is None or (limit_repeat_words is not None and find in limit_repeat_words):
                repeat.append(find)
                if index == 3:
                    has_start_repeat = True
    return repeat, has_start_repeat


def analyse_modal_genscp_by_file_v2(in_dir, out_dir, txt_dir, prefix, modals=["嗯", "呃"], has_id=False):
    '''
    分析 in_dir 中的句子, 将分析结果存入 out_dir, 将有语气词、无英文、无开头语气词的句子写入 txt_dir 中, 命名规则为 prefix_index(行数) 或 prefix_id \n
    文件每一行:text 或 id   text
    '''
    assert os.path.isfile(in_dir), "{} is not a file".format(in_dir)

    if not os.path.isdir(out_dir):
        os.mkdir(out_dir)
    
    if not os.path.isdir(txt_dir):
        os.mkdir(txt_dir)

    f_in = open(in_dir, 'r')
    lines = f_in.readlines()

    utts, has_english_list, no_modal_list, start_modal_list, get = [], [], [], [], []

    for index, line in tqdm(enumerate(lines)):
        
        if has_id:
            id = line.split('\t')[0]
            line = line.split('\t')[1]
        else:
            id = str(index)

        utts.append(id)
        
        has_modal = False
        has_english = False
        has_start_modal = False

        line = line.strip()

        if re.search(r'[A-Za-z]', line):
            has_english = True
        
        for modal in modals:
            find_i = line.find(modal)
            if find_i != -1:
                has_modal = True
                if find_i == 0:
                    has_start_modal = True

        if not has_modal:
            no_modal_list.append(id)

        if has_english:
            has_english_list.append(id)

        if has_start_modal:
            start_modal_list.append(id)

        if has_modal and not has_english and not has_start_modal:
            get.append(id)
            txt_out = open(os.path.join(txt_dir, prefix + "_" + str(id) + ".txt"), 'w')
            txt_out.write(str(id) + "\t" + line)
            txt_out.flush()
            txt_out.close()   

    scpTools.utts2scp(has_english_list, os.path.join(out_dir, "all_has_english.lst"))

    scpTools.utts2scp(no_modal_list, os.path.join(out_dir, "no_montal.lst"))

    scpTools.utts2scp(start_modal_list, os.path.join(out_dir, "has_start_montal.lst"))
    
    scpTools.utts2scp(get, os.path.join(out_dir, "all-modal-no_english-no_start_montal.lst"))

    f = open(os.path.join(out_dir, "info"), 'w')
    f.write("utts:{}, has_english:{}, no_modal:{}, start_modal:{}, get:{}".format(
            len(utts), len(has_english_list), len(no_modal_list), len(start_modal_list), len(get)))
    f.flush()
    f.close()

    return utts, has_english_list, no_modal_list, start_modal_list, get


def analyse_modal_genscp_by_dir_v2(in_dir, out_dir, txt_dir, prefix, modals=["嗯", "呃"], has_id=False):
    '''
    分析 in_dir 中的句子, 将分析结果存入 out_dir, 将有语气词、无英文、无开头语气词的句子写入 txt_dir 中, 命名规则为 prefix_id \n
    文件每一行:text 或 id   text
    '''

    if not os.path.isdir(out_dir):
        os.mkdir(out_dir)
    
    if not os.path.isdir(txt_dir):
        os.mkdir(txt_dir)

    files = scpTools.genscp_in_list(in_dir)

    utts, has_english_list, no_modal_list, start_modal_list, get = [], [], [], [], []

    for file in tqdm(files):

        f = open(os.path.join(in_dir, file + ".txt"))
        line = f.readline().strip()

        if has_id:
            id = line.split('\t')[0]
            line = line.split('\t')[1]
        else:
            id = file

        utts.append(id)
        
        has_modal = False
        has_english = False
        has_start_modal = False

        line = line.strip()
        
        if re.search(r'[A-Za-z]', line):
            has_english = True
        
        for modal in modals:
            find_i = line.find(modal)
            if find_i != -1:
                has_modal = True
                if find_i == 0:
                    has_start_modal = True

        if  not has_modal:
            no_modal_list.append(id)

        if has_english:
            has_english_list.append(id)

        if has_start_modal:
            start_modal_list.append(id)

        if has_modal and not has_english and not has_start_modal:
            get.append(id)
            txt_out = open(os.path.join(txt_dir, prefix + "_" + str(id) + ".txt"), 'w')
            txt_out.write(str(id) + "\t" + line)
            txt_out.flush()
            txt_out.close()   

    scpTools.utts2scp(has_english_list, os.path.join(out_dir, "all_has_english.lst"))

    scpTools.utts2scp(no_modal_list, os.path.join(out_dir, "no_montal.lst"))

    scpTools.utts2scp(start_modal_list, os.path.join(out_dir, "has_start_montal.lst"))
    
    scpTools.utts2scp(get, os.path.join(out_dir, "all-modal-no_english-no_start_montal.lst"))

    f = open(os.path.join(out_dir, "info"), 'w')
    f.write("utts:{}, has_english:{}, no_modal:{}, start_modal:{}, get:{}".format(
            len(utts), len(has_english_list), len(no_modal_list), len(start_modal_list), len(get)))
    f.flush()
    f.close()

    return utts, has_english_list, no_modal_list, start_modal_list, get


def analyse_modal_genscp_by_file_v1(in_dir, out_dir, txt_dir, prefix):
    '''
    分析 in_dir 中的句子, 将分析结果存入 out_dir, 将有语气词、无英文、无开头语气词的句子写入 txt_dir 中, 命名规则为 prefix_index(行数) \n
    文件每一行:text 
    '''
    assert os.path.isfile(in_dir), "{} is not a file".format(in_dir)

    if not os.path.isdir(out_dir):
        os.mkdir(out_dir)
    
    if not os.path.isdir(txt_dir):
        os.mkdir(txt_dir)

    f_in = open(in_dir, 'r')
    lines = f_in.readlines()

    utts, has_english_list, no_modal_list, start_modal_list, get = [], [], [], [], []

    for index, line in tqdm(enumerate(lines)):

        id = str(index)

        utts.append(id)
        
        has_modal = False
        has_english = False
        has_start_modal = False

        line = line.strip()        
        for i, t in enumerate(line):
            if re.search(r'[A-Za-z]', t):
                has_english = True
            if t in ["嗯", "呃"]:
                has_modal = True
                if i == 0:
                    has_start_modal = True

        if not has_modal:
            no_modal_list.append(id)

        if has_english:
            has_english_list.append(id)

        if has_start_modal:
            start_modal_list.append(id)

        if has_modal and not has_english and not has_start_modal:
            get.append(id)
            txt_out = open(os.path.join(txt_dir, prefix + "_" + str(id) + ".txt"), 'w')
            txt_out.write(str(id) + "\t" + line)
            txt_out.flush()
            txt_out.close()   

    scpTools.utts2scp(has_english_list, os.path.join(out_dir, "all_has_english.lst"))

    scpTools.utts2scp(no_modal_list, os.path.join(out_dir, "no_montal.lst"))

    scpTools.utts2scp(start_modal_list, os.path.join(out_dir, "has_start_montal.lst"))
    
    scpTools.utts2scp(get, os.path.join(out_dir, "all-modal-no_english-no_start_montal.lst"))

    f = open(os.path.join(out_dir, "info"), 'w')
    f.write("utts:{}, has_english:{}, no_modal:{}, start_modal:{}, get:{}".format(
            len(utts), len(has_english_list), len(no_modal_list), len(start_modal_list), len(get)))
    f.flush()
    f.close()

    return utts, has_english_list, no_modal_list, start_modal_list, get


def analyse_modal_genscp_by_dir_v1(base_dir):
    '''
    分析 base_dir 的 /txts 中的句子, 将分析结果存入 /file_lst \n
    每个文件: id    text 
    '''
    in_dir = os.path.join(base_dir, "txts")
    out_dir = os.path.join(base_dir, "file_lst")

    if not os.path.isdir(out_dir):
            os.mkdir(out_dir)

    utts = scpTools.genscp_in_list(in_dir)
    scpTools.utts2scp(utts, os.path.join(base_dir, "file_lst/all.lst"))

    has_english_list, no_modal_list, start_modal_list, get = [], [], [], []

    for utt in tqdm(utts):
        
        has_modal = False
        has_english = False
        has_start_modal = False

        f = open(os.path.join(in_dir, utt + ".txt"))
        line = f.readline().strip()
        assert len(line.split('\t')) == 2, "line should be 'id text', but get: {}".format(line)
        
        id, text = line.split('\t')
        for i, t in enumerate(text):
            if re.search(r'[A-Za-z]', t):
                has_english = True
            if t in ["嗯", "呃"]:           
                has_modal = True
                if i == 0:
                    has_start_modal = True

        if  not has_modal:
            no_modal_list.append(utt)

        if has_english:
            has_english_list.append(utt)

        if has_start_modal:
            start_modal_list.append(utt)

        if has_modal and not has_english and not has_start_modal:
            get.append(utt)

    scpTools.utts2scp(has_english_list, os.path.join(base_dir, "file_lst/all_has_english.lst"))

    scpTools.utts2scp(scpTools.exclude_scp(utts, has_english_list), os.path.join(base_dir, "file_lst/all_no_english.lst"))

    scpTools.utts2scp(no_modal_list, os.path.join(base_dir, "file_lst/no_montal.lst"))

    scpTools.utts2scp(start_modal_list, os.path.join(base_dir, "file_lst/has_start_montal.lst"))
    
    scpTools.utts2scp(get, os.path.join(base_dir, "file_lst/all-modal-no_english-no_start_montal.lst"))

    f = open(os.path.join(base_dir, "info"), 'w')
    f.write("utts:{}, has_english:{}, no_modal:{}, start_modal:{}, get:{}".format(
            len(utts), len(has_english_list), len(no_modal_list), len(start_modal_list), len(get)))
    f.flush()
    f.close()

    return utts, has_english_list, no_modal_list, start_modal_list, get


def analyse_modal_distribution_from_txts(in_dir, utts):
    '''
    在 in_dir 的 utts 中找到含有语气词的句子, 并分析语气词出现的位置与频率 \n
    每个文件: id    text 
    '''
    modal_word_in_start, modal_word_in_mid, modal_word_in_end = 0, 0, 0
    modal_sent_num, no_modal_sent_num = 0, 0
    modal_sent_in_start, modal_sent_in_mid, modal_sent_in_end = 0, 0, 0
    word_num = 0
    sent_num = len(utts)
    
    for utt in tqdm(utts):
        
        has_modal = False
        has_modal_in_mid = False

        f = open(os.path.join(in_dir, utt + ".txt"))
        line = f.readline().strip()
        assert len(line.split('\t')) == 2, "line should be 'id text', but get: {}".format(line)
        
        id, text = line.split('\t')
        for i, t in enumerate(text):
            word_num += 1
            if t in ["嗯", "呃"]:                
                has_modal = True
                if i == 0:
                    modal_word_in_start += 1
                    modal_sent_in_start += 1
                elif i == len(text) - 1:
                    modal_word_in_end += 1
                    modal_sent_in_end += 1
                else:
                    modal_word_in_mid += 1
                    has_modal_in_mid = True
        if has_modal:
            modal_sent_num += 1
        else:
            no_modal_sent_num += 1

        if has_modal_in_mid:
            modal_sent_in_mid += 1
    
    print("word_num: {}, modal_word_in_start: {}, modal_word_in_mid: {}, modal_word_in_end: {}".format(word_num, modal_word_in_start, modal_word_in_mid, modal_word_in_end))
    print("sent_num: {}, modal_num: {}, no_modal_num: {}, modal_sent_in_start: {}, modal_sent_in_mid: {}, modal_sent_in_end: {}".format(sent_num, modal_sent_num, no_modal_sent_num, modal_sent_in_start, modal_sent_in_mid, modal_sent_in_end))


def find_modal_in_start(in_dir, utts):
    '''
    在 in_dir 的 utts 中找到第一个字为语气词的句子, 返回 name list \n
    每个文件: id    text 
    '''
    names = []
    
    for utt in tqdm(utts):

        f = open(os.path.join(in_dir, utt + ".txt"))
        line = f.readline().strip()
        assert len(line.split('\t')) == 2, "line should be 'id text', but get: {}".format(line)
        
        id, text = line.split('\t')
        if text[0] in ["嗯", "呃"]:
            names.append(utt)

    return names


def find_no_modal(in_dir, utts):
    '''
    在 in_dir 的 utts 中找到不含有语气词的句子 \n
    每个文件: id    text 
    '''
    names = []
    
    for utt in tqdm(utts):
        
        no_modal = True

        f = open(os.path.join(in_dir, utt + ".txt"))
        line = f.readline().strip()
        assert len(line.split('\t')) == 2, "line should be 'id text', but get: {}".format(line)
        
        id, text = line.split('\t')
        for i, t in enumerate(text):
            if t in ["嗯", "呃"]:                
                no_modal = False
                break

        if no_modal:
            names.append(utt)
    
    return names


def find_modal(in_dir, utts):
    '''
    在 in_dir 的 utts 中找到含有语气词的句子, 返回 name list \n
    每个文件: id    text 
    '''
    name_list = []
    
    for utt in tqdm(utts):
        f = open(os.path.join(in_dir, utt + ".txt"))
        line = f.readline().strip()
        assert len(line.split('\t')) == 2, "line should be 'id text', but get: {}".format(line)
        id, text = line.split('\t')
        for t in text:
            if t in ["嗯", "呃"]:
                name_list.append(id)
                break
    
    return name_list


def find_alpha(in_dir, utts, seq='\t'):
    '''
    在 in_dir 的 utts 中找到含有英语的句子, 返回 name list \n
    每个文件: id    text 
    '''
    name_list = []
    
    for utt in tqdm(utts):
        f = open(os.path.join(in_dir, utt + ".txt"))
        line = f.readline().strip()
        assert len(line.split(seq)) == 2, "line should be 'id text', but get: {}".format(line)
        id, text = line.split(seq)
        for t in text:
            if re.search(r'[A-Za-z]', t):
                # print(t)
                name_list.append(id)
                break
    
    return name_list


def find_number(in_dir, utts, seq='\t', from_label=False):
    '''
    在 in_dir 的 utts 中找到含有数字的句子, 返回 name list \n
    输入可以是label, 也可以是txt, 输入label时, 每一列用\t分割, 且第一列为字序列
    每个文件: id    text 
    '''
    name_list = []
    
    for utt in tqdm(utts):
        if from_label:
            with open(os.path.join(in_dir, utt + ".lab"), "r", encoding='utf-8') as f:
                lab = f.readlines()
                word = [x.strip().split("\t")[0] for x in lab]
                text = "".join(word)
        else:
            f = open(os.path.join(in_dir, utt + ".txt"))
            line = f.readline().strip()
            assert len(line.split(seq)) == 2, "line should be 'id text', but get: {}".format(line)
            id, text = line.split(seq)
        for t in text:
            if re.search(r'[0-9]', t):
                # print(t)
                name_list.append(utt)
                break
    
    return name_list


def addtag_from_syllabel_v3(in_dir , out_dir, insert_set):
    '''
    从原始syllabel中删除插入词，并将插入词作为label
    '''
    if not os.path.isdir(out_dir):
        os.mkdir(out_dir)

    utts = scpTools.genscp_in_list(in_dir)
    for utt in tqdm(utts):
        letters, tones, prosodys = labelTools.read_label(os.path.join(in_dir, utt + ".lab"))
        
        tags = [0] * len(letters)
        del_index = []

        text = ''.join(letters)
        for insert in insert_set:
            del_i = tools.find_substr(text, insert)
            for i in del_i:
                tags[i-1] = insert
                del_index.extend(range(i, i + len(insert)))
        
        del_index = set(del_index)

        new_letters = [letters[i] for i in range(len(letters)) if i not in del_index]
        new_tones = [tones[i] for i in range(len(tones)) if i not in del_index]
        new_prosodys = [prosodys[i] for i in range(len(prosodys)) if i not in del_index]
        new_tags = [tags[i] for i in range(len(tags)) if i not in del_index]
        
        labelTools.write_label(os.path.join(out_dir, utt + ".lab"), [new_letters, new_tones, new_prosodys, new_tags])


def addtag_from_syllabel_v2(in_dir, out_dir, modal2tag, add_sil=False):
    '''
    解析syllabel, 在语气字的前一个字加上tag, 并删掉语气字，语气字可以为多个字 \n
    根据 add_sil 判断是否要加 sil_S 和 sil_E
    '''
    if not os.path.isdir(out_dir):
        os.mkdir(out_dir)

    utts = scpTools.genscp_in_list(in_dir)
    for utt in tqdm(utts):
        letters, tones, prosodys = labelTools.syllabel2list(os.path.join(in_dir, utt + ".lab"))
        
        tags = [0] * len(letters)
        del_index = []

        text = ''.join(letters)
        for modal in modal2tag:
            del_i = tools.find_substr(text, modal)
            for i in del_i:
                tags[i-1] = modal2tag[modal]
                del_index.extend(range(i, i + len(modal)))
        
        del_index = set(del_index)

        new_letters = [letters[i] for i in range(len(letters)) if i not in del_index]
        new_tones = [tones[i] for i in range(len(tones)) if i not in del_index]
        new_prosodys = [prosodys[i] for i in range(len(prosodys)) if i not in del_index]
        new_tags = [tags[i] for i in range(len(tags)) if i not in del_index]

        if add_sil:
            new_letters.insert(0, "sil_S")
            new_tones.insert(0, "S")
            new_prosodys.insert(0, "0")
            new_tags.insert(0, "0")
            letters.append("sil_E")
            new_tones.append("S")
            new_prosodys.append("0")
            new_tags.append("0")
        
        labelTools.write_label(os.path.join(out_dir, utt + ".lab"), [new_letters, new_tones, new_prosodys, new_tags])


def addtag_from_syllabel_v1(in_dir, out_dir, letter2tag, add_sil=False):
    '''
    解析syllabel, 在语气字的前一个字加上tag, 并删掉语气字 \n
    根据 add_sil 判断是否要加 sil_S 和 sil_E
    '''
    if not os.path.isdir(out_dir):
        os.mkdir(out_dir)

    utts = scpTools.genscp_in_list(in_dir)
    for utt in tqdm(utts):
        letters, tones, prosodys = labelTools.syllabel2list(os.path.join(in_dir, utt + ".lab"))
        tags = []
        del_index = []

        if add_sil:
            letters.insert(0, "sil_S")
            tones.insert(0, "S")
            prosodys.insert(0, "0")

        for index, letter in enumerate(letters):
            if letter in letter2tag and index > 0:
                tags[-1] = letter2tag[letter]
                del_index.append(index)
            tags.append("0")

        del_num = len(del_index)
        for i in range(del_num):
            letters.pop(del_index[-1 - i])
            tones.pop(del_index[-1 - i])
            prosodys.pop(del_index[-1 - i])
            tags.pop(del_index[-1 - i])

        if add_sil:
            letters.append("sil_E")
            tones.append("S")
            prosodys.append("0")
            tags.append("0")
        
        labelTools.write_label(os.path.join(out_dir, utt + ".lab"), [letters, tones, prosodys, tags])


def delmodal_from_syllabel(in_dir, out_dir, letter2tag):
    '''
    解析syllabel, 删掉语气字
    '''
    if not os.path.isdir(out_dir):
        os.mkdir(out_dir)

    utts = scpTools.genscp_in_list(in_dir)
    for utt in tqdm(utts):
        word, seg_tag, prosody = labelTools.syllabel2list(os.path.join(in_dir, utt + ".lab"))
        del_index = []

        for index, letter in enumerate(word):
            if letter in letter2tag:
                del_index.append(index)

        del_num = len(del_index)
        for i in range(del_num):
            word.pop(del_index[-1 - i])
            seg_tag.pop(del_index[-1 - i])
            prosody.pop(del_index[-1 - i])
        
        labelTools.write_label(os.path.join(out_dir, utt + ".lab"), [word, seg_tag, prosody])


def check_syllabel(in_dir):
    '''
    检查syllabel, 统计语气词出现在不同seg_tag的频率
    '''
    seg_tag2num = {}

    utts = scpTools.genscp_in_list(in_dir)
    for utt in tqdm(utts):
        word, seg_tag, prosody, tag = labelTools.syllabel2list_has_tag(os.path.join(in_dir, utt + ".lab"))

        for index in range(len(word)):
            if not seg_tag[index] in seg_tag2num:
                seg_tag2num[seg_tag[index]] = 0
            if tag[index] != "0":
                seg_tag2num[seg_tag[index]] += 1

    print(seg_tag2num)
        

def add_modal(self, sent_list, tag_list):
    new_sents = []
    tag2word = {"1":"嗯", "2":"呃"}

    for id_sent, sent in enumerate(sent_list):
        new_sent = sent
        add_index = []
        add_tag = []
        for id_tag, tag in enumerate(tag_list[id_sent]):
            if tag != 0:
                add_index.append(id_tag)
                add_tag.append(tag)

        add_num = len(add_index)
        for i in range(add_num):
            new_sent.insert(add_index[-1 - i] + 1, tag2word[str(add_tag[-1 - i])])
        new_sents.append(new_sent)
    
    return new_sents


def huiting_find_modal(in_dir, dic):
    '''
    从慧听 id.text.scp 文件中发现 <F> <N> <*> <k>，统计每个标签的name_list \n
    输入样例： \n
    31014040350.wav 但是跟你们一起唱我也是很开心的 \n
    31014040351.wav 毕竟可以<*>出来 \n
    '''
    assert os.path.isfile(in_dir), "{} is not a file".format(in_dir)

    lines = open(in_dir, 'r').readlines()
    for line in lines:
        id, text = line.strip().split('\t')
        for index, word in enumerate(text):
            if word == '<':
                key = text[index + 1]
                if key in dic:
                    dic[key].append(id)
                else:
                    dic[key] = [id]
    return dic


def huiting_get_utt2spk(in_dir, lst):
    '''
    从慧听 id.speaker.scp 文件中读取说话人AB信息，并返回字符串 \n
    输入样例： \n
    31017200005.wav A \n
    31017200006.wav A \n
    31017200007.wav B \n
    31017200008.wav B \n
    输出样例： \n
    31017200005 3101720A \n
    31017200006 3101720A \n
    31017200007 3101720B \n
    31017200008 3101720B \n
    '''
    assert os.path.isfile(in_dir), "{} is not a file".format(in_dir)

    lines = open(in_dir, 'r').readlines()
    for line in lines:
        if len(line.strip().split('\t')) != 2:
            print("error line: {}".format(line))
            continue
        id, spk = line.strip().split('\t')
        lst.append(id.split('.')[0] + "\t" + id[:7] + spk)
        
    return lst


def huiting_load_spk2sex(utt2sex_path):
    '''
    读取utt2sex，返回字典 \n
    输入样例： \n
    3100035	男	女 \n
    3100056	女	女 \n
    3100059	女	女 \n
    输出样例： \n
    {3100035A:男, 3100035B:女, 3100056A:女, 3100056B:女, 3100059A:女, 3100059B:女}
    '''
    utt2sex = {}
    with open(utt2sex_path, encoding='utf-8') as f:
        for line in f.readlines():
            utt, sexa, sexb = line.strip().split("\t")
            utt2sex[utt+"A"] = sexa
            utt2sex[utt+"B"] = sexb
    return utt2sex


def huiting_get_text(utt, text_dir):
    '''
    根据所给的文件名，从文本中找到所在行，并返回
    '''
    lines = open(text_dir, 'r').readlines()
    for line in lines:
        if len(line.strip().split('\t')) != 2:
            print("error line: {}".format(line))
            continue
        name, text = line.strip().split('\t')
        if name.startswith(utt):
            return utt + "\t" + text + "\n"
    print("no text {}".format(utt))
    exit(0)


def huiting_random_F(in_dir, out_dir, modal_list, has_number=False, has_number_out_dir=None):
    '''
    对输入文本中含有的<F>，随机替换为语气词 \n
    输入样例： \n
    31002220046     <F>初步计划的是去长白山旅行 \n
    31002220065     <F>纯粹为了购物而旅行的话就 \n
    31002220069     <F>一种风格 \n
    输出样例： \n
    31002220046     嗯初步计划的是去长白山旅行 \n
    31002220065     呃纯粹为了购物而旅行的话就 \n
    31002220069     嗯一种风格 \n
    或 \n
    31002220046     1嗯初步计划的是去长白山旅行 \n
    31002220065     2呃纯粹为了购物而旅行的话就 \n
    31002220069     1嗯一种风格 \n
    '''
    modal_num = len(modal_list)
    lines = open(in_dir, 'r').readlines()
    out = open(out_dir, 'w')
    if has_number:
        out_num = open(has_number_out_dir, 'w')

    for line in lines:

        if len(line.strip().split('\t')) != 2:
            print("error line: {}".format(line))
            continue

        name, text = line.strip().split('\t')
        ran = random.randint(0, modal_num-1)

        text1 = text.replace("<F>", modal_list[ran])
        out.write(name + '\t' + text1 + '\n')

        if has_number:
            text2 = text.replace("<F>", str(ran+1) + modal_list[ran])
            out_num.write(name + '\t' + text2 + '\n')
    
    out.flush()
    out.close()
    out_num.flush()
    out_num.close()


def spon_genlabel(in_dir, out_dir):
    '''
    根据 in_dir 下的 label, 生成spon所用的label, 并输出到 out_dir
    '''
    if not os.path.isdir(out_dir):
        os.mkdir(out_dir)

    utts = scpTools.genscp_in_list(in_dir)
    for utt in tqdm(utts):
        read = open(os.path.join(in_dir, utt + ".lab"), 'r').readlines()
        write = open(os.path.join(out_dir, utt + ".lab"), 'w')
        for line in read:
            phone = line.split('\t')[0]
            pos = line.split('\t')[2]
            newline = line.strip()
            newline += "\tN\tN\tN\t0\n"
            write.write(newline)
        write.flush()
        write.close()


def modal_del_number(in_dir, out_dir):
    '''
    删除indir中每个文本中用来标注语气词的数字
    输入样例：
    F0312001014	2哦真的很高。
    '''
    utts = scpTools.genscp_in_list(in_dir)
    if not os.path.isdir(out_dir):
        os.mkdir(out_dir)

    for utt in tqdm(utts):
        line = open(os.path.join(in_dir, utt + ".txt"), 'r').readlines()
        id = line[0].split('\t')[0].strip()
        text = line[0].split('\t')[1].strip()
        new_text = re.sub(r'\d', r'', text)
        
        out = open(os.path.join(out_dir, utt + ".txt"), 'w')
        out.write(id + '\t' + new_text)
        out.flush()
        out.close()

def main():

    mode = 24

    if mode == 0:
        '''
        /home/work_nfs4_ssd/hzli/data/nlp/biaobei-3w
        /home/work_nfs4_ssd/hzli/data/nlp/hw_conversation/chat/chat-female
        /home/work_nfs4_ssd/hzli/data/nlp/hw_conversation/chat/chat-male
        /home/work_nfs4_ssd/hzli/data/nlp/Train_Ali_near
        /home/work_nfs4_ssd/hzli/data/nlp/lm_text/gather
        '''
        return "some file utils"
    elif mode == 1:
        in_dir = "/home/work_nfs4_ssd/hzli/data/nlp/DB-TTS-C-G-021-20220323/modal_test/syllabel_labels"
        out_dir = "/home/work_nfs4_ssd/hzli/data/nlp/DB-TTS-C-G-021-20220323/modal_test/syllabel_labels_nosil_hastag"
        letter2tag = {"嗯": 1, "呃": 2}
        addtag_from_syllabel_v1(in_dir, out_dir, letter2tag)
    elif mode == 2:
        in_dir = "/home/work_nfs5_ssd/hzli/data/spontaneous/syllabel_labels"
        out_dir = "/home/work_nfs5_ssd/hzli/data/spontaneous/syllabel_no_modal"
        letter2tag = {"嗯": 1, "呃": 2}
        delmodal_from_syllabel(in_dir, out_dir, letter2tag)
    elif mode == 4:
        in_dir = "/home/work_nfs5_ssd/hzli/data/nlp/Train_Ali_near/txts"
        utts = scpTools.genscp_in_list(in_dir)
        print('\n'.join(find_modal(in_dir, utts)))
    elif mode == 5:
        in_dir = "/home/work_nfs5_ssd/hzli/data/spontaneous/txts"
        utts = scpTools.scp2list("/home/work_nfs5_ssd/hzli/data/spontaneous/file_lst/all.lst")
        scpTools.utts2scp(find_alpha(in_dir, utts), "/home/work_nfs5_ssd/hzli/data/spontaneous/file_lst/all_has_english.lst")
    elif mode == 6:
        in_dir = "/home/work_nfs5_ssd/hzli/nlp/sequence_labeling/data/corpus_3w/syllabel_no_modal_add_sil"
        check_syllabel(in_dir)
    elif mode == 7:
        in_dir = "/home/work_nfs5_ssd/hzli/data/nlp/all_data/txts"
        utts = scpTools.genscp_in_list(in_dir)
        analyse_modal_distribution_from_txts(in_dir, utts)
    elif mode == 8:
        base_dir = "/home/work_nfs4_ssd/hzli/data/nlp/DB-TTS-C-G-021-20220323/modal_test"
        utts, has_english, no_modal, start_modal, get = analyse_modal_genscp_by_dir_v1(base_dir)
        print("utts:{}, has_english:{}, no_modal:{}, start_modal:{}, get:{}".format(
            len(utts), len(has_english), len(no_modal), len(start_modal), len(get)))
    elif mode == 10:
        base_dir = "/home/work_nfs4_ssd/hzli/data/nlp/lm_text"
        for name in ["mandarin/biaobeislt_text", "mandarin/data2500_text",  "mandarin/data6200_text",  
                    "mandarin/data6400_text",  "mandarin/data7500_text",  "mandarin/datatang700_text",  
                    "mandarin/huiting1000_text",  "maneng/aishell0056_text",  "maneng/asru700_text",  
                    "maneng/biaobei900_text",  "maneng/chonglang_text", "maneng/dt300_text",  
                    "maneng/huitingmix_text",  "maneng/ManEng_3G_cut"]:
            print(name)
            in_dir = os.path.join("/home/work_nfs4_ssd/hzli/data/nlp/lm_text", name)
            out_dir = os.path.join("/home/work_nfs4_ssd/hzli/data/nlp/lm_text", name + "_filelst")
            txt_dir = "/home/work_nfs4_ssd/hzli/data/nlp/lm_text/txts_get"
            analyse_modal_genscp_by_file_v1(in_dir, out_dir, txt_dir, name.split('/')[1])
    elif mode == 11:
        base_dir = "/home/backup_nfs4/ghliu/ASR_data/Huiting"
        dic = {}
        for see in tqdm(os.listdir(base_dir)):
            in_dir = os.path.join(base_dir, see, see + ".text.scp")
            jsonTools.save_json(dic, "/home/work_nfs5_ssd/hzli/kkcode/tmp_hw/all.json")
            dic = huiting_find_modal(in_dir, dic)
    elif mode == 12:
        f = open("/home/work_nfs5_ssd/hzli/kkcode/tmp_hw/all.json", 'r')
        dic = json.load(f)
        for key in dic:
            if key in ["/"]:
                lst = [i.split('.')[0] for i in dic[key]]
                scpTools.list2scp(lst, os.path.join("/home/work_nfs5_ssd/hzli/kkcode/tmp_hw", "inverse\.lst"))
                continue
            lst = [i.split('.')[0] for i in dic[key]]
            scpTools.list2scp(lst, os.path.join("/home/work_nfs5_ssd/hzli/kkcode/tmp_hw", key + ".lst"))
    elif mode == 13:
        base_dir = "/home/backup_nfs4/ghliu/ASR_data/Huiting"
        lst = []
        for see in tqdm(os.listdir(base_dir)):
            in_dir = os.path.join(base_dir, see, see + ".speaker.scp")
            lst = huiting_get_utt2spk(in_dir, lst)
        scpTools.list2scp(lst, "/home/work_nfs5_ssd/hzli/kkcode/tmp_hw/utt2spk")                
    elif mode == 14:
        # tmp
        utts = scpTools.scp2list("/home/work_nfs5_ssd/hzli/kkcode/tmp_hw/F_exclude.lst")
        utt2spk = spkTools.load_utt2spk("/home/work_nfs5_ssd/hzli/kkcode/tmp_hw/utt2spk")
        dic = {}
        for utt in utts:
            if not utt in utt2spk:
                print(utt)
                continue
            spk = utt2spk[utt]
            if spk in dic:
                dic[spk] += 1
            else:
                dic[spk] = 1
        jsonTools.save_json(dic, "/home/work_nfs5_ssd/hzli/kkcode/tmp_hw/F_exclude_spk2num.json")
    elif mode == 15:
        f = open("/home/work_nfs5_ssd/hzli/kkcode/tmp_hw/F_exclude_spk2num.json", 'r')
        spk2num = json.load(f)
        new_dic = {}
        spk2sex = huiting_load_spk2sex("/home/work_nfs5_ssd/hzli/kkcode/tmp_hw/spk2sex")
        for spk in spk2num:
            if spk.endswith("AB"):
                continue
            if spk2sex[spk] == "女":
                new_dic[spk] = spk2num[spk]
                if spk2num[spk] > 300:
                    print("\"{}\":{}".format(spk, spk2num[spk]))
        jsonTools.save_json(new_dic, "/home/work_nfs5_ssd/hzli/kkcode/tmp_hw/F_exclude_female_spk2num.json")
    elif mode == 16:
        utt2spk = spkTools.load_utt2spk("/home/work_nfs5_ssd/hzli/kkcode/tmp_hw/utt2spk")
        F_exclude = scpTools.scp2list("/home/work_nfs5_ssd/hzli/kkcode/tmp_hw/F_exclude.lst")
        utts = []
        spks = ["3100222B", "3101417B", "3101422B", "3101437A", "3101450B", "3101471A", "3101525B", "3101533A", "3101550A", "3101552A", "3101631A", "3101705B", "3101714A", "3101730A", "3101741B", "3101745B"]
        for utt in F_exclude:
            if utt in utt2spk and utt2spk[utt] in spks:
                utts.append(utt)
        scpTools.list2scp(utts, "/home/work_nfs5_ssd/hzli/kkcode/tmp_hw/huiting.lst")
    elif mode == 17:
        utts = scpTools.scp2list("/home/work_nfs5_ssd/hzli/kkcode/tmp_hw/select_220323/huiting.lst")
        data_dir = "/home/work_nfs5_ssd/hzli/acoustic_model/modal_tacotron_for_hw_v1/data/huiting/huiting"
        out_dir = "/home/work_nfs5_ssd/hzli/acoustic_model/modal_tacotron_for_hw_v1/data/huiting"

        text_out_dir = os.path.join(out_dir, "back-text.txt")
        text = open(text_out_dir, 'w')

        for utt in tqdm(utts):
            name = utt[:7]
            wav_dir = os.path.join(data_dir, name, "recorderSPK", utt + ".wav")
            wav_out_dir = os.path.join(out_dir, "48k_wavs", utt + ".wav")
            os.system("ln -s " + wav_dir + " " + wav_out_dir)
            
            text_dir = os.path.join(data_dir, name, name + ".text.scp")
            t = huiting_get_text(utt, text_dir)
            text.write(t)
        text.flush()
        text.close()
    elif mode == 18:
        spk2utt = json.load(open("/home/work_nfs5_ssd/hzli/kkcode/tmp_hw/info/spk2utt.json"))
        spks = ["3100222B", "3101417B", "3101422B", "3101437A", "3101450B", "3101471A", "3101525B", "3101533A", "3101550A", "3101552A", "3101631A", "3101705B", "3101714A", "3101730A", "3101741B", "3101745B"]
        has_select = scpTools.scp2list("/home/work_nfs5_ssd/hzli/kkcode/tmp_hw/select/F_exclude.lst")
        exclude = scpTools.scp2list("/home/work_nfs5_ssd/hzli/kkcode/tmp_hw/select/exclude.lst")
        spk2utt_new = {}        
        for spk in spks:
            utts = spk2utt[spk]
            utts = scpTools.exclude_scp(utts, exclude)
            spk2utt_new[spk] = tools.control_data_num_0(utts, has_select, 500)
            for i in spk2utt_new[spk]:
                if i in exclude:
                    print("error utt: {}".format(i))
                    
        for spk in spks:
            print("{}:{}".format(spk, len(spk2utt_new[spk])))
        jsonTools.save_json(spk2utt_new, "/home/work_nfs5_ssd/hzli/kkcode/tmp_hw/select_220323/spk2utt.json")
        utts = spkTools.trans_spk2utt_to_utt(spk2utt_new)
        scpTools.list2scp(utts, "/home/work_nfs5_ssd/hzli/kkcode/tmp_hw/select_220323/huiting.lst")
    elif mode == 19:
        in_dir = "/home/work_nfs5_ssd/hzli/data/db1_new-5000ju/labs"
        out_dir = "/home/work_nfs5_ssd/hzli/data/db1_new-5000ju/labels_modal"
        spon_genlabel(in_dir, out_dir)
    elif mode == 20:
        in_dir = "/home/work_nfs5_ssd/hzli/acoustic_model/modal_tacotron_for_hw_v1/data/huiting/back-text.txt"
        out_dir = "/home/work_nfs5_ssd/hzli/acoustic_model/modal_tacotron_for_hw_v1/data/huiting/text.txt"
        has_number_out_dir = "/home/work_nfs5_ssd/hzli/acoustic_model/modal_tacotron_for_hw_v1/data/huiting/text_hasnumber.txt"
        modal = ["嗯", "呃"]
        huiting_random_F(in_dir, out_dir, modal, has_number=True, has_number_out_dir=has_number_out_dir)
    elif mode == 21:
        in_dir = "/home/work_nfs5_ssd/hzli/acoustic_model/modal_tacotron_for_hw_v1/data/mix/test/txts_hasnumber/"
        out_dir = "/home/work_nfs5_ssd/hzli/acoustic_model/modal_tacotron_for_hw_v1/data/mix/test/txts"
        modal_del_number(in_dir, out_dir)
    elif mode == 22:
        tmp = 3
        if tmp == 0:
            base_dir = "/home/work_nfs4_ssd/hzli/data/nlp/biaobei-3w"
            in_dir = os.path.join(base_dir, "origin_data.txt")
            out_dir = os.path.join(base_dir, "for-jiushi_nage", "filelst")
            txt_dir = os.path.join(base_dir, "for-jiushi_nage", "txts")
            analyse_modal_genscp_by_file_v2(in_dir, out_dir, txt_dir, "biaobei-3w", modals=["就是", "那个"], has_id=True)
        elif tmp == 1:
            # base_dir = "/home/work_nfs4_ssd/hzli/data/nlp/hw_conversation/chat/chat-female"
            # prefix = "hw-chat-female"
            base_dir = "/home/work_nfs4_ssd/hzli/data/nlp/Train_Ali_near"
            prefix = "Train_Ali_near"
            in_dir = os.path.join(base_dir, "txts")
            if not os.path.isdir(os.path.join(base_dir, "for-jiushi_nage")):
                os.mkdir(os.path.join(base_dir, "for-jiushi_nage"))
            out_dir = os.path.join(base_dir, "for-jiushi_nage", "filelst")
            txt_dir = os.path.join(base_dir, "for-jiushi_nage", "txts")
            analyse_modal_genscp_by_dir_v2(in_dir, out_dir, txt_dir, prefix, modals=["就是", "那个"], has_id=True)
        elif tmp == 2:
            base_dir = "/home/work_nfs4_ssd/hzli/data/nlp/lm_text"
            for name in ["mandarin/biaobeislt_text", "mandarin/data2500_text",  "mandarin/data6200_text",  
                        "mandarin/data6400_text",  "mandarin/data7500_text",  "mandarin/datatang700_text",  
                        "mandarin/huiting1000_text",  "maneng/aishell0056_text",  "maneng/asru700_text",  
                        "maneng/biaobei900_text",  "maneng/chonglang_text", "maneng/dt300_text",  
                        "maneng/huitingmix_text",  "maneng/ManEng_3G_cut"]:
                print(name)
                in_dir = os.path.join("/home/work_nfs4_ssd/hzli/data/nlp/lm_text", name)
                if not os.path.isdir(os.path.join(base_dir, "gather", "for-jiushi_nage")):
                    os.mkdir(os.path.join(base_dir, "gather", "for-jiushi_nage"))
                if not os.path.isdir(os.path.join(base_dir, "gather", "for-jiushi_nage", "filelst")):
                    os.mkdir(os.path.join(base_dir, "gather", "for-jiushi_nage", "filelst"))
                out_dir = os.path.join(base_dir, "gather", "for-jiushi_nage", "filelst", name.split('/')[1] + "_filelst")
                txt_dir = os.path.join(base_dir, "gather", "for-jiushi_nage/txts_get")
                analyse_modal_genscp_by_file_v2(in_dir, out_dir, txt_dir, name.split('/')[1], modals=["就是", "那个"], has_id=False)
        elif tmp == 3:
            in_dir = "/home/work_nfs4_ssd/hzli/data/nlp/all_data_for-jiushi_nage/syllabel_labels"
            out_dir = "/home/work_nfs4_ssd/hzli/data/nlp/all_data_for-jiushi_nage/syllabel_labels_nosil_hastag"
            modal2tag = {"就是": 1, "那个": 2}
            addtag_from_syllabel_v2(in_dir, out_dir, modal2tag)
    elif mode ==23:
        in_dir = "/home/work_nfs4_ssd/hzli/data/nlp/test/npu_testB/syllabel_labels"
        out_dir = in_dir + "_nosil_hastag"
        modal2tag = {"就是": 1, "那个": 2}
        addtag_from_syllabel_v2(in_dir, out_dir, modal2tag)  


if __name__ == "__main__":
    main()

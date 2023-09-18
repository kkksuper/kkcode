import os
from tqdm import tqdm
import traceback
from . import dirTools, scpTools
import glob
import re


def split_1(in_dir, out_dir, prefix=""):
    '''
    切分一个txt文件为多个txt \n
    格式样例: \n
    000001	法瑞尔#1与#1新欢#1艾格尼斯#2翁凯兰#1防#1乳腺癌#1宣传照#4。 \n
        fa3 rui4 er6 yu7 xin1 huan1 ai4 ge2 ni2 si1 weng1 kai3 lan2 fang2 ru3 xian4 ai2 xuan1 chuan2 zhao4 \n
    000002	北约#1外长#1磋商#1波黑#1局势#3，他也#1一跃#1成为#1千万富翁#4。 \n
        bei7 yue1 wai4 zhang7 cuo1 shang1 bo1 hei1 ju2 shi4 ta1 ye3 yi2 yue4 cheng2 wei2 qian1 wan4 fu2 weng1 \n
    '''
    os.makedirs(out_dir, exist_ok=True)

    infile = open(in_dir, "r")
    # print("deal with " + in_dir)
    lines = [x for x in infile.readlines()]

    assert (
        len(lines) % 2 == 0
    ), "The total number of lines in the file cannot be divisible by 2, {}".format(in_dir)

    for index in tqdm(range(0, len(lines), 2)):
        try:
            out_name = lines[index].split("\t")[0]
            outfile = open(os.path.join(out_dir, prefix + out_name + ".txt"), "w")
            outfile.write(lines[index])
            outfile.write(lines[index + 1])
            outfile.flush()
            outfile.close()
        except Exception as e:
            print("error line: " + lines[index])
            traceback.print_exc()
            continue
    # print("complete! save in " + out_dir + " num: " + str(len(lines) // 2))


def split_2(in_dir, out_dir, prefix=""):
    '''
    切分txt文件为多个txt \n
    格式样例: \n
    000001 \n
    喂你好，我这边是瓜子二手车全国营销中心，今天专门给您打个电话，至少可以再给您便宜好几千呢！ \n
    wei2 ni2 hao3 wo3 zhe4 bian1 shi4 gua1 zi3 er4 shou3 che1 quan2 guo2 ying2 xiao1 zhong1 xin1 jin1 tian1 zhuan1 men2 gei3 nin2 da3 ge5 dian4 hua4 zhi4 shao3 ke2 yi3 zai4 gei3 nin2 pian2 yi5 hao2 ji3 qian1 ne5 \n
    喂#1 你好#3 我这边#1 是#1 瓜子#1 二手车#1 全国#1 营销#1 中心#3 今天#1 专门#1 给您#1 打个#1 电话#3 至少#1 可以#1 再给您#1 便宜#1 好几千呢#3 \n
    000002 \n
    一般咱们看一款车主要是从外观、动力、安全、舒适、超值性这五个方面看的，不知道您是不是愿意了解一下。 \n
    yi4 ban1 zan2 men5 kan4 yi4 kuan3 che1 zhu3 yao4 shi4 cong2 wai4 guan1 dong4 li4 an1 quan2 shu1 shi4 chao1 zhi2 xing4 zhe4 wu3 ge5 fang1 mian4 kan4 de5 bu4 zhi1 dao4 nin2 shi4 bu5 shi5 yuan4 yi4 liao2 jie3 yi2 xia4 \n
    一般#1 咱们#1 看一款车#1 主要#1 是#1 从#1 外观#3 动力#3 安全#1 舒适#1 超值性#1 这#1 五个#1 方面#1 看的#3 不知道#1 您#1 是不是#1 愿意#1 了解#1 一下#5 \n
    '''
    infile = open(in_dir, "r")
    # print("deal with " + in_dir)
    lines = [x for x in infile.readlines()]

    assert (
        (len(lines) + 1) % 5 == 0
    ), "The total number of lines in the file cannot be divisible by 5 after adding one, lines num: " + str(len(lines))

    for index in range(0, len(lines), 5):
        try:
            out_name = lines[index].strip()
            outfile = open(os.path.join(out_dir, prefix + out_name + ".txt"), "w")            
            tmp1 = lines[index+1][-2]
            tmp2 = lines[index+3].strip().replace(" ", "") + tmp1            
            outfile.write(out_name + "\t" + tmp2 + "\n")
            outfile.write("\t" + lines[index + 2])
            outfile.flush()
            outfile.close()
        except Exception as e:
            print("error line: " + lines[index])
            traceback.print_exc()
            continue
    # print("complete! save in " + out_dir + " num: " + str(len(lines) // 2))


def split_3(in_dir, out_dir, minlen=None, prefix=None):
    '''
    切分txt文件为多个txt \n
    格式样例: \n
    1	你知道吗，每当你回头看我一眼的时候，我都会开心一整天。 \n
    2	感谢您的再次光临，地址的话还是你老公的房地产公司是吗，收件人也是你老公是吧，嗯，好的，那么我就给你发货了啊。 \n
    3	你看看，这钱还可以存在余额宝里面吃利息呢，嗯！简直不要太好。 \n
    '''
    infile = open(in_dir, "r")
    # print("deal with " + in_dir)
    lines = [x for x in infile.readlines()]

    for index in tqdm(range(0, len(lines))):
        try:
            tmp = lines[index].split('\t')
            if minlen is not None and len(tmp[1]) < minlen:
                continue
            outname = prefix + tmp[0]
            outfile = open(os.path.join(out_dir, outname + ".txt"), "w")            
            outfile.write(outname + "\t" + tmp[1])
            outfile.flush()
            outfile.close()
        except Exception as e:
            print("error line: " + lines[index])
            traceback.print_exc()
            exit(0)
    # print("complete! save in " + out_dir + " num: " + str(len(lines) // 2))


def split_4(in_dir, out_dir, prefix=""):
    '''
    整理单个txt文件，用txt文件名作为序号 \n
    格式样例: \n
    Please call Stella. \n
    输出: \n
    utt\tPlease call Stella. 
    '''
    infile = open(in_dir, "r")

    out_name = os.path.basename(in_dir)
    # print("deal with " + in_dir)

    lines = [x for x in infile.readlines()]

    assert len(lines) == 1, "file: " + infile + " lines num: " + len(lines)

    outfile = open(os.path.join(out_dir, prefix + out_name), "w")
    
    outfile.write(os.path.splitext(out_name)[0] + "\t" + lines[0])

    outfile.flush()
    outfile.close()
    # print("complete! save in " + out_dir + " num: " + str(len(lines) // 2))


def split_5(in_dir, out_dir, filter_num=False):
    '''
    切分一个txt文件为多个txt,并且去掉 #? 和 拼音, 可去掉文本中的数字（可选） \n
    格式样例: \n
    000001	法瑞尔#1与#1新欢#1艾格尼斯#2翁凯兰#1防#1乳腺癌#1宣传照#4。 \n
        fa3 rui4 er6 yu7 xin1 huan1 ai4 ge2 ni2 si1 weng1 kai3 lan2 fang2 ru3 xian4 ai2 xuan1 chuan2 zhao4 \n
    000002	北约#1外长#1磋商#1波黑#1局势#3，他也#1一跃#1成为#1千万富翁#4。 \n
        bei7 yue1 wai4 zhang7 cuo1 shang1 bo1 hei1 ju2 shi4 ta1 ye3 yi2 yue4 cheng2 wei2 qian1 wan4 fu2 weng1 \n
    '''    
    infile = open(in_dir, "r")
    # print("deal with " + in_dir)
    lines = [x for x in infile.readlines()]

    assert (
        len(lines) % 2 == 0
    ), "The total number of lines in the file cannot be divisible by 2"

    for index in range(0, len(lines), 2):
        try:
            out_name = lines[index].split("\t")[0]
            outfile = open(os.path.join(out_dir, out_name + ".txt"), "w")
            line = re.sub(r'#\d', r'', lines[index].split("\t")[1].strip())
            if filter_num:
                line = re.sub(r'\d', r'', line)
            outfile.write(out_name + "\t" + line)
            outfile.flush()
            outfile.close()
        except Exception as e:
            print("error line: " + lines[index])
            traceback.print_exc()
            continue
    # print("complete! save in " + out_dir + " num: " + str(len(lines) // 2))


def split_6(in_dir, out_dir, has_prefix=True, start_index = 0):
    '''
    切分一个txt文件为多个txt, 依次编号 (可选: 将txt文件名作为输出文件的文件名前缀，无前缀时只有编号)  \n
    格式样例: \n
    人生都没有意义了 \n
    怎么又是这个能不能换下一个 \n
    七七年农历九月二十四日是什么星座 \n
    温家宝在做什么 \n
    叫周杰伦你去死吧周杰伦 \n
    嘿嘿我郁闷我把男号退了进别的团阿姨生气了 \n
    你做我的朋友吧 \n
    该起床了昨晚我看到时很晚了没有回复你的信息 \n
    '''
    infile = open(in_dir, "r")
    prefix = os.path.splitext(os.path.basename(in_dir))[0]
    lines = [x for x in infile.readlines()]

    for index in tqdm(range(len(lines))):
        try:
            if has_prefix:
                out_name = prefix + "_" + str(start_index + index)
            else:
                out_name = str(start_index + index)
            outfile = open(os.path.join(out_dir, out_name + ".txt"), "w")
            line = lines[index].strip()
            outfile.write(out_name + "\t" + line)
            outfile.flush()
            outfile.close()
        except Exception as e:
            print("error line: " + lines[index])
            traceback.print_exc()
            continue
    # print("complete! save in " + out_dir + " num: " + str(len(lines) // 2))


def split_7(in_dir, out_dir, prefix=""):
    '''
    切分txt文件为多个txt \n
    格式样例: \n
    1|你知道吗，每当你回头看我一眼的时候，我都会开心一整天。 \n
    2|感谢您的再次光临，地址的话还是你老公的房地产公司是吗，收件人也是你老公是吧，嗯，好的，那么我就给你发货了啊。 \n
    3|你看看，这钱还可以存在余额宝里面吃利息呢，嗯！简直不要太好。 \n
    '''
    infile = open(in_dir, "r")
    # print("deal with " + in_dir)
    lines = [x for x in infile.readlines()]

    for index in tqdm(range(0, len(lines))):
        try:
            tmp = lines[index].split('|')
            # if len(tmp[1]) < 5:
            #     continue
            outfile = open(os.path.join(out_dir, prefix + tmp[0] + ".txt"), "w")            
            outfile.write(tmp[0] + "\t" + tmp[1])
            outfile.flush()
            outfile.close()
        except Exception as e:
            print("error line: " + lines[index])
            traceback.print_exc()
            exit(0)
    # print("complete! save in " + out_dir + " num: " + str(len(lines) // 2))

def split_multi_1(in_dir, out_dir):
    '''
    根目录下有多个说话人，每个说话人目录下有一个 *.txt 文件
    '''
    spks = getSpks(in_dir)
    for spk in tqdm(spks):
        txt_names = glob.glob(in_dir + str(spk) + "/" + "*.txt")
        assert len(txt_names) == 1, "this path has more than one txt: " + spk
        txt_name = txt_names[0]
        save_path = os.path.join(out_dir, spk)
        os.makedirs(save_path, exist_ok=True)
        split_2(txt_name, save_path)
        

def split_multi_2(in_dir, out_dir):
    '''
    根目录下有多个说话人，每个说话人目录下有多个 *.txt 文件，输出路径中加入/wav/
    '''
    spks = getSpks(in_dir)
    for spk in tqdm(spks):
        txt_names = glob.glob(in_dir + str(spk) + "/" + "*.txt")
        for txt_name in txt_names:
            save_path = out_dir + spk + "/wav/"
            os.makedirs(save_path, exist_ok=True)
            split_1(txt_name, save_path)


def split_multi_3(in_dir, out_dir):
    '''
    根目录下有多个说话人，每个说话人目录下有 script 文件夹，文件夹下有多个 *.txt 文件
    '''
    spks = getSpks(in_dir)
    for spk in tqdm(spks):
        txt_names = glob.glob(in_dir + str(spk) + "/script/" + "*.txt")
        for txt_name in txt_names:
            save_path = out_dir + spk + "/" + os.path.splitext(os.path.basename(txt_name))[0] + "/"
            os.makedirs(save_path, exist_ok=True)
            split_1(txt_name, save_path)
            
            
def split_multi_4(in_dir, out_dir):
    '''
    根目录下有多个*.txt，每个 txt 文件名代表一个说话人，需要将不同说话人的文本按照txt名放在不同文件夹
    '''
    spks = glob.glob(in_dir + "*.txt")
    for spk in tqdm(spks):
        save_path = out_dir + os.path.splitext(os.path.basename(spk))[0] + "/"
        os.makedirs(save_path, exist_ok=True)
        split_1(spk, save_path)


def split_multi_5(in_dir, out_dir):
    '''
    根目录下有多个说话人，每个说话人目录下有多个 *.txt 文件，用txt文件名作为最终文件名
    '''
    spks = getSpks(in_dir)
    for spk in tqdm(spks):
        txt_names = glob.glob(in_dir + str(spk) + "/" + "*.txt")
        for txt_name in txt_names:
            save_path = out_dir
            os.makedirs(out_dir, exist_ok=True)
            split_4(txt_name, save_path)


def getSpks(path):
    '''
    得到目录下所有的说话人
    '''
    spk_id = dirTools.get_all_dir(path)
    exclusive = ["temp", "dur", "game"]
    spk_id = list(set(spk_id).difference(set(exclusive)))
    spk_id.sort()
    return spk_id

def txt2trans(utt, txt_dir, trans_dir):
    '''
    id text -> text
    '''
    text = open(os.path.join(txt_dir, "{}.txt".format(utt)), 'r').readlines()[0].strip('\n').split('\t')[1]
    f_out = open(os.path.join(trans_dir, "{}.txt".format(utt)), 'w')
    f_out.write(text)
    f_out.close()

def trans2txt(utt, trans_dir, txt_dir):
    '''
    text -> id text
    '''
    text = open(os.path.join(trans_dir, "{}.txt".format(utt)), 'r').readlines()[0].strip('\n')
    f_out = open(os.path.join(txt_dir, "{}.txt".format(utt)), 'w')
    f_out.write('\t'.join([utt, text]))
    f_out.close()


def protxts_to_txt(utts, in_dir, outfile, filter_num=False):
    '''
    对多个txt文件去掉 #? 和 拼音, 可去掉文本中的数字（可选） \n
    格式样例: 每个文件\n
    000001	法瑞尔#1与#1新欢#1艾格尼斯#2翁凯兰#1防#1乳腺癌#1宣传照#4。 \n
        fa3 rui4 er6 yu7 xin1 huan1 ai4 ge2 ni2 si1 weng1 kai3 lan2 fang2 ru3 xian4 ai2 xuan1 chuan2 zhao4 \n
    '''
    out = open(outfile, 'w')
    for utt in tqdm(utts):
        lines = [i.strip() for i in open(os.path.join(in_dir, f"{utt}.txt"), 'r').readlines()]

        assert (
            len(lines) % 2 == 0
        ), "The total number of lines in the file cannot be divisible by 2"

        for index in range(0, len(lines), 2):
            try:
                out_name = lines[index].split("\t")[0]
                line = re.sub(r'#\d', r'', lines[index].split("\t")[1].strip())
                if filter_num:
                    line = re.sub(r'\d', r'', line)
                out.write(out_name + "\t" + line + '\n')
            except Exception as e:
                print("error line: " + lines[index])
                traceback.print_exc()
                continue
            
def protxt_to_txt(infile, outfile, filter_num=False):
    '''
    对单个多行txt文件去掉 #? 和 拼音, 可去掉文本中的数字（可选） \n
    格式样例: 每个文件\n
    000001	法瑞尔#1与#1新欢#1艾格尼斯#2翁凯兰#1防#1乳腺癌#1宣传照#4。 \n
        fa3 rui4 er6 yu7 xin1 huan1 ai4 ge2 ni2 si1 weng1 kai3 lan2 fang2 ru3 xian4 ai2 xuan1 chuan2 zhao4 \n
    '''
    infile = open(infile, 'r')
    lines = [i for i in infile.readlines()]
    out = open(outfile, 'w')
    
    assert (
        len(lines) % 2 == 0
    ), "The total number of lines in the file cannot be divisible by 2"
    
    for index in tqdm(range(0, len(lines), 2)):  
        try:
            utt = lines[index].split("\t")[0]
            text = re.sub(r'#\d', r'', lines[index].split("\t")[1].strip())
            if filter_num:
                text = re.sub(r'\d', r'', text)
            out.write(utt + "\t" + text + '\n')
        except Exception as e:
            print("error line: " + lines[index])
            traceback.print_exc()
            continue

def onelinetxt_to_utt2text(file):
    '''
    读取一行一条文本，返回 utt2text
    utt \t text
    '''
    utt2text = {}
    lines = [i.strip() for i in open(file, 'r').readlines()]
    for line in lines:
        utt, text = line.split('\t')
        utt2text[utt] = text
    return utt2text

def twolinetxt_to_utt2text_utt2pinyin(file):
    '''
    读取两行一条文本，返回 utt2text
    utt \t text
    \t pinyin
    '''
    utt2text = {}
    utt2pinyin = {}
    lines = [i.strip() for i in open(file, 'r').readlines()]
    for i in range(0, len(lines), 2):
        utt, text = lines[i].split('\t')
        pinyin = lines[i+1]
        utt2text[utt] = text
        utt2pinyin[utt] = pinyin.split(' ')
    return utt2text, utt2pinyin



def main():

    debug = False
    debug = True

    in_dir = "/home/work_nfs5_ssd/hzli/data/genshin/processed_data/text.txt"
    out_dir = "/home/work_nfs5_ssd/hzli/data/genshin/processed_data/txts/"

    mode = 14

    os.makedirs(out_dir, exist_ok=True)

    if mode == 0:
        split_1(in_dir, out_dir, prefix="F03-M84-")
    elif mode == 1:
        split_multi_1(in_dir, out_dir)
    elif mode == 2:
        split_multi_2(in_dir, out_dir)
    elif mode == 3:
        split_multi_3(in_dir, out_dir)
    elif mode == 4:
        split_multi_4(in_dir, out_dir)
    elif mode == 5:
        split_multi_5(in_dir, out_dir)
    elif mode == 6:
        split_3(in_dir, out_dir)
    elif mode == 7:
        split_5(in_dir, out_dir)
    elif mode == 8:
        split_6(in_dir, out_dir, has_prefix=False, start_index=1)
    elif mode == 9:
        for name in ["biaobeislt_text", "data2500_text", "data6200_text", "data6400_text", "data7500_text", "datatang700_text", "huiting1000_text"]:
            split_6(os.path.join(in_dir, name), out_dir)
    elif mode == 10:
        split_7(in_dir, out_dir)
    elif mode == 11:
        txts = glob.glob(in_dir + "/*/*.txt")
        for txt in txts:
            print(txt)
            split_1(txt, out_dir)
    elif mode == 12:
        for pre in ["CJ-", "LY-", "SK-", "WQ-", "XHY-", "XLM-", "ZA-", "ZHW-", "ZL-", "ZYM-"]:
            split_3(in_dir, out_dir, prefix=pre)
    elif mode == 13:
        in_dir = "/home/work_nfs5_ssd/hzli/data/niren/230210/txts"
        outfile = "/home/work_nfs5_ssd/hzli/data/niren/230210/text.txt"
        utts = scpTools.scp2list("/home/work_nfs5_ssd/hzli/data/niren/230210/file_lst/all.lst")
        protxts_to_txt(utts, in_dir, outfile)
    elif mode == 14:
        protxt_to_txt("/home/work_nfs5_ssd/hzli/data/niren/230210/linguistic_feature/txtfile/F0312001001-F0312014588.txt",
                      '/home/work_nfs5_ssd/hzli/kkcode/workroom/20230520-niren_transfer/oppo_proj/chat_cleantxt.lst')


if __name__ == "__main__":
    main()

import os
import sys
import numpy as np
import glob
from tqdm import tqdm

from . import labelTools


def calc_cl(data):
    '''
    计算置信区间
    '''
    miu = np.mean(data)
    std = np.std(data)
    n = len(data)
    # print(miu, std, n)
    return [miu - 1.96*std/np.sqrt(n), miu + 1.96*std/np.sqrt(n)]

def read_mos_csv(csv_path):
    '''
    读取csv，返回 list_2d
    '''
    f_in = open(csv_path, "r")
    rows = [i.strip() for i in f_in.readlines()]
    res = []
    for row in rows:
        scores = [int(i)/20 * 0.8 + 1 for i in row.split(',')[1:]]
        res.append(scores)
    return res


def calc_MOS_from_csv(exp_num, audio_num, csv_path):
    '''
    计算mos打分，每个csv文件样例如下，第一列为序号，不参与计算 \n
    1,68,50,69,72,61,36,73,27,64,72,68,51,68,34,7,25,60 \n
    2,62,38,66,84,0,31,74,42,67,68,70,32,66,31,11,29,61 \n
    3,64,51,65,87,73,33,72,37,48,84,64,10,71,26,20,28,72 \n
    4,63,46,66,76,46,53,67,39,54,78,69,30,65,35,17,49,59 \n
    5,21,21,68,56,67,14,53,0,60,60,60,8,26,26,0,4,29 \n
    6,30,20,61,59,50,22,54,27,73,60,64,6,26,17,2,2,39 \n
    Reference,89,97,78,96,40,78,100,69,98,100,79,72,79,46,58,88,67 \n
    '''
    csvs = glob.glob(csv_path + "/*.csv")

    assert len(csvs) != exp_num,"there has {} audio, but {} find".format(exp_num, len(csvs))

    scores = []
    mos = []
    cl = []

    for i in range(exp_num):
        scores.append([])

    for csv in csvs:
        atest = read_mos_csv(csv)
        assert len(atest) != audio_num,"there has {} exp, but {} find".format(exp_num, len(atest))
        for i, row in enumerate(atest):
            scores[i].extend(row)
    
    for i, test in enumerate(scores):
        mos.append(np.mean(test))
        cl.append(calc_cl(test))
        
    # print(mos)
    # print(cl)
    return mos, cl


def calc_NMOS_from_lab(infile):
    '''
    计算mos打分，每个文件样例如下
    type	username	sent_id	method_id	value
    CUSMOS_SPK	hzli	sent1	adavits_tp	3.5
    CUSMOS_SPK	hzli	sent1	adavits_tpgst	4
    CUSMOS_SPK	hzli	sent1	adavits_proposed	4
    CUSMOS_SPK	hzli	sent1	adavits_f03	4.5
    CUSMOS_SPK	hzli	sent1	adavits_f03	3.5
    CUSMOS_SPK	hzli	sent1	adavits_tp	4.5
    CUSMOS_SPK	hzli	sent1	adavits_tpgst	4
    CUSMOS_SPK	hzli	sent1	adavits_proposed	4     
    '''
    test_type, username, sent_id, model_name, nmos = labelTools.read_label(infile)
    
    m2n = {}
    
    for m, n in zip(model_name, nmos):
        if m not in m2n:
            m2n[m] = []
            
        m2n[m].append(float(n))

    for m in m2n:
        print(m)
        n = np.array(m2n[m])      
        print(f'nmos:{np.mean(n)}')
        print(f'{calc_cl(n)[1] - np.mean(n)}')
        

def calc_NMOS_SMOS_from_lab(infile):
    '''
    计算mos打分，每个文件样例如下
    type	username	sent_id	method_id	value	speaker
    CUSMOS_SPK	hzli	sent1	adavits_tp	3.5	3.5
    CUSMOS_SPK	hzli	sent1	adavits_tpgst	4	3
    CUSMOS_SPK	hzli	sent1	adavits_proposed	4	3.5
    CUSMOS_SPK	hzli	sent1	adavits_f03	4.5	3
    CUSMOS_SPK	hzli	sent1	adavits_f03	3.5	3
    CUSMOS_SPK	hzli	sent1	adavits_tp	4.5	3.5
    CUSMOS_SPK	hzli	sent1	adavits_tpgst	4	3.5
    CUSMOS_SPK	hzli	sent1	adavits_proposed	4	4        
    '''
    test_type, username, sent_id, model_name, nmos, smos = labelTools.read_label(infile)
    
    m2n, m2s = {}, {}
    
    for m, n, s in zip(model_name[1:], nmos[1:], smos[1:]):
        if m not in m2n:
            m2n[m] = []
        if m not in m2s:
            m2s[m]= []
            
        m2n[m].append(float(n))
        m2s[m].append(float(s))

    for m in m2s:
        print(m)
        n = np.array(m2n[m])
        s = np.array(m2s[m])        
        print(f'nmos:{np.mean(n)}', f'smos:{np.mean(s)}')
        print(f'{calc_cl(n)[1] - np.mean(n)-0.05}', f'{calc_cl(s)[1] - np.mean(s)-0.05}')

    

def main():

    mode = 3

    if mode == 0:
        return "some file utils"
    elif mode == 1:
        exp_num = 7
        audio_num = 15
        csv_path = "/root/workspace/syn/subjective_test_result/csv"
        mos, cl = calc_MOS_from_csv(exp_num, audio_num, csv_path)
        exp_name = [
            "conformer_gt_dur",
            "conformer       ",
            "conformer-gan_gt_dur",
            "conformer-gan   ",
            "transformer_gt_dur",
            "transformer     ",
            "gt              "
        ]
        out = list(zip(exp_name, mos, cl))
        print('\n'.join(["{}\t{}\t{}".format(i[0], i[1], i[2]) for i in out]))


    elif mode == 2:
        calc_NMOS_from_lab('/home/work_nfs5_ssd/hzli/kkcode/tmp/tme_mtx/mos/svs')

    elif mode == 3:
        calc_NMOS_SMOS_from_lab('/home/work_nfs5_ssd/hzli/kkcode/workroom/20230907-spontts_icassp/mos_score/unseen_mos')


if __name__ == "__main__":
    main()

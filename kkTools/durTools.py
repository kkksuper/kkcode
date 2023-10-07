import os
from tqdm import tqdm
import glob
import numpy as np
from . import labelTools, scpTools

def load_dur(dur_path):
    '''
    从时长文件得到每行总时长
    '''
    durs = np.sum(np.loadtxt(dur_path), axis=1)
    durs = [int(i) for i in durs]
    return durs

def load_dur_in_second(dur_path, sr=24000, hop_size=256):
    '''
    从时长文件得到每行总时长
    '''
    frame_time = 1.0 / sr * hop_size
    durs = np.sum(np.loadtxt(dur_path), axis=1)
    durs = [int(i) for i in durs]
    durs[0] += 4
    print(durs)
    for i in range(len(durs)):
        if i != 0:
            durs[i] += durs[i-1]
    durs.insert(0, 0)
    durs = [round(dur * frame_time, 4) for dur in durs]
    durs = [(durs[i-1], dur) for i,dur in enumerate(durs) if i != 0]
    return durs

def write_dur(dur, out_path):
    '''
    给定时长 list，写到指定路径，格式 x 0 0 0 0
    '''
    fout = open(out_path, 'w')
    fout.write('\n'.join(str(i) + " 0 0 0 0" for i in dur))

def durConvert(in_dir,
               out_dir,
               old_sr=16000,
               old_hop_size=200,
               new_sr=24000,
               new_hop_size=256):
    '''
    将提取到的 old_hop_size 的时长转化为 new_hop_size 的时长 \n
    '''
    if not os.path.isdir(out_dir):
        os.mkdir(out_dir)

    file_names = glob.glob(in_dir + "/*.lab")
    file_names.sort()

    for index in tqdm(range(len(file_names))):
        f = open(file_names[index], "r")
        dur = []
        more_old_time = 0

        for line in f.readlines():
            cur_old_time = 1.0 / old_sr * sum(
                int(i) for i in line.split(" ")) * old_hop_size
            cur_time = cur_old_time + more_old_time
            cur_new_frame = cur_time * new_sr // new_hop_size
            dur.append(cur_new_frame)
            more_old_time = cur_time - cur_new_frame * new_hop_size / new_sr
            more_old_time = more_old_time if more_old_time >= 0 else 0

        fout = open(os.path.join(out_dir,
                                 os.path.split(file_names[index])[1]), 'w')
        fout.write('\n'.join(str(i) + " 0 0 0 0" for i in dur))
        fout.flush()
        fout.close()

def fix_htk_dur(utts, in_dir, out_dir):
    '''
    htk dur is less than nice mel, because padding reflect when extract mel, so dur should +2 in first and last phone
    '''
    os.makedirs(out_dir, exist_ok=True)
    for utt in tqdm(utts):
        duration = load_dur(os.path.join(in_dir, utt + ".lab"))
        duration[0] += 2
        duration[-1] += 2
        write_dur(duration, os.path.join(out_dir, utt + ".lab"))


def calc_dur_std(utts, in_dir):
    '''
    统计 dur 标准差，返回平均值
    '''
    std = []
    for utt in tqdm(utts):
        durs = load_dur(os.path.join(in_dir, f'{utt}.lab'))
        std.append(np.std(np.array(durs)))
    return np.mean(np.array(std)), np.std(np.array(std))

def main():

    mode = 0

    if mode == 0:
        print(np.sum(load_dur('/home/work_nfs4_ssd/hzli/tts_aligner/egs_230720_bigdata16k/arctic/dur/VCTK_raw_p256_255.lab')))
        print(np.sum(load_dur('/home/work_nfs5_ssd/hzli/kkcode/tmp/durs/24k_300/VCTK_raw_p256_255.lab')))
        print(np.sum(load_dur('/home/work_nfs7/ykli/data/vits/bigdata/durs/VCTK_raw_p256_255.lab')))
        # /home/work_nfs5_ssd/hzli/data/big_data/16k/durs
        return "some utils"
    elif mode == 1:
        in_dir = "/home/work_nfs5_ssd/hzli/kkcode/tmp/durs/16k_200"
        out_dir = "/home/work_nfs5_ssd/hzli/kkcode/tmp/durs/24k_300"
        old_hop_size = 200
        new_hop_size = 300
        durConvert(in_dir, out_dir, old_sr=16000, new_sr=24000, old_hop_size=old_hop_size, new_hop_size=new_hop_size)
    elif mode == 2:
        dur_path = "/home/work_nfs5_ssd/hzli/data/niren/220924/durs_htk_notrim"
        lab_path = "/home/work_nfs5_ssd/hzli/data/niren/220924/labs_with_rest_speed_liandu_emph_emotion_modal_dur+4"
        utt  = 'F03-M83-0313062077.lab'
        inpath = os.path.join(dur_path, utt)
        dur = load_dur_in_second(inpath)
        lab = labelTools.read_label(os.path.join(lab_path, utt))
        phone, tag = lab[0], lab[-1]
        print(len(phone), len(dur))
        for p, t, d in zip(phone, tag, dur):
            print(f"{p}\t{t}\t{d[0]}\t{d[1]}")
        '''
        ['F03-M83-0313057001', 'F03-M84-0313006100', 'F03-M84-0313078114', 'F03-M84-0313078102', 'F03-M84-0313039047', 'F03-M83-0313018187', 'F03-M83-0313048019', 'F03-M84-0313033154', 'F03-M83-0313038010', 'F03-M84-0313020017', 'F03-M84-0313084025', 'F03-M83-0313024128', 'F03-M83-0313002038', 'F03-M84-0313003024', 'F03-M83-0313005013', 'F03-M83-0313021086', 'F03-M83-0313056117', 'F03-M83-0313019060', 'F03-M83-0313052195', 'F03-M83-0313051001', 'F03-M83-0313070156', 'F03-M83-0313066042', 'F03-M83-0313070055', 'F03-M83-0313021165', 'F03-M83-0313035098', 'F03-M83-0313035067', 'F03-M83-0313041022', 'F03-M83-0313017254', 'F03-M83-0313031051', 'F03-M83-0313070121', 'F03-M83-0313075043', 'F03-M84-0313043123', 'F03-M83-0313029001', 'F03-M84-0313047022', 'F03-M83-0313076082', 'F03-M83-0313057047', 'F03-M83-0313038196', 'F03-M83-0313070133', 'F03-M84-0313078108', 'F03-M83-0313007025', 'F03-M84-0313006209', 'F03-M84-0313036060', 'F03-M84-0313066066', 'F03-M83-0313062077', 'F03-M83-0313041026', 'F03-M83-0313038213', 'F03-M83-0313043033', 'F03-M84-0313033061', 'F03-M83-0313012025', 'F03-M84-0313016005', 'F03-M83-0313027328', 'F03-M84-0313072035', 'F03-M83-0313051039', 'F03-M84-0313006529', 'F03-M84-0313008027', 'F03-M84-0313038103']
        '''

        '''
        ['F03-M83-0313002038', 'F03-M83-0313005013', 'F03-M83-0313017254', 'F03-M83-0313021165', 'F03-M83-0313027328', 'F03-M83-0313029001', 'F03-M83-0313031051', 'F03-M83-0313035067', 'F03-M83-0313035098', 'F03-M83-0313038196', 'F03-M83-0313038213', 'F03-M83-0313041022', 'F03-M83-0313041026', 'F03-M83-0313048019', 'F03-M83-0313051001', 'F03-M83-0313051039', 'F03-M83-0313052195', 'F03-M83-0313056117', 'F03-M83-0313057001', 'F03-M83-0313057047', 'F03-M83-0313062077', 'F03-M83-0313066042', 'F03-M83-0313070055', 'F03-M83-0313070121', 'F03-M83-0313070133', 'F03-M83-0313070156', 'F03-M83-0313075043', 'F03-M83-0313076082', 'F03-M84-0313003024', 'F03-M84-0313008027', 'F03-M84-0313016005', 'F03-M84-0313033061', 'F03-M84-0313033154', 'F03-M84-0313038103', 'F03-M84-0313043123', 'F03-M84-0313047022', 'F03-M84-0313066066', 'F03-M84-0313072035', 'F03-M84-0313078102', 'F03-M84-0313078108']
        '''

    elif mode == 3:
        # in_dir = "/home/work_nfs5_ssd/hzli/data/niren/230210/durs_htk_trim15"
        # out_dir = "/home/work_nfs5_ssd/hzli/data/niren/230210/durs_htk_trim15"
        in_dir = "/home/work_nfs5_ssd/hzli/data/htk/230211_biaobei_final_notrim/acoustic_features/duration_targets"
        out_dir = "/home/work_nfs5_ssd/hzli/data/niren/230210/durs_htk_notrim"
        utts = scpTools.genscp_in_list(in_dir)
        fix_htk_dur(utts, in_dir, out_dir)

    elif mode == 4:
        in_dir = '/home/work_nfs5_ssd/hzli/data/niren/transfer/durs'
        # utts = scpTools.scp2list('/home/work_nfs5_ssd/hzli/data/niren/transfer/file_lst/train_db6_1w.lst') # (3.9388480018455905, 0.9482847128589976)
        utts = scpTools.scp2list('/home/work_nfs5_ssd/hzli/data/niren/transfer/file_lst/train_03_1w.lst') # (5.761301738397871, 2.8010908482479056)
        print(in_dir)
        print(calc_dur_std(utts, in_dir))

if __name__ == "__main__":
    main()

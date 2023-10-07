import os
from tqdm import tqdm
import glob
import pretty_midi
from . import labelTools

def get_num_from_pos(pho_pos_in_note):
    """
    音素在音节中的位置，得到每个音素所在的音节的音素数
    """
    num = []
    tmp = -1

    for i in pho_pos_in_note:
        if i == "0":
            if tmp != -1:
                for j in range(1, tmp + 1, 1):
                    num[-j] = tmp
            tmp = 1
        else:
            tmp = tmp + 1
        num.append(tmp)

    # 处理最后一个且pos非0的音素
    for j in range(1, tmp + 1, 1):
        num[-j] = tmp

    return num


def label2line_visinger(label_path, wav_path="", f0_path=""):
    """
    将一个label文件转化为visinger用的list的其中一行
    """

    assert os.path.isfile(label_path) and label_path.endswith(".lab"), (
        "label path seems to be wrong: " + label_path
    )

    fuxi_pitch_set = [
        "C0", "C1", "C2", "C3", "C4", "C5", "C6", "C#0/Db0", "C#1/Db1", "C#2/Db2", "C#3/Db3", "C#4/Db4", "C#5/Db5", "C#6/Db6", "D0", "D1", "D2", "D3", "D4", "D5", "D6", "D#0/Eb0", "D#1/Eb1", "D#2/Eb2", "D#3/Eb3", "D#4/Eb4", "D#5/Eb5", "D#6/Eb6", "E0", "E1", "E2", "E3", "E4", "E5", "E6", "F0", "F1", "F2", "F3", "F4", "F5", "F6", "F#0/Gb0", "F#1/Gb1", "F#2/Gb2", "F#3/Gb3", "F#4/Gb4", "F#5/Gb5", "F#6/Gb6", "G0", "G1", "G2", "G3", "G4", "G5", "G6", "G#0/Ab0", "G#1/Ab1", "G#2/Ab2", "G#3/Ab3", "G#4/Ab4", "G#5/Ab5", "G#6/Ab6", "A0", "A1", "A2", "A3", "A4", "A5", "A6", "A#0/Bb0", "A#1/Bb1", "A#2/Bb2", "A#3/Bb3", "A#4/Bb4", "A#5/Bb5", "A#6/Bb6", "B0", "B1", "B2", "B3", "B4", "B5", "B6", "rest",
    ]
    
    phone, pitch, slur, pho_pos_in_note, num, score_duration, real_duration = labelTools.read_label(label_path)

    name = os.path.splitext(os.path.basename(label_path))[0]
    wav_path_w = wav_path + name + ".wav"
    phone_w = " ".join(phone)
    pitchid_w = " ".join([str(fuxi_pitch_set.index(i)) for i in pitch])
    slur_w = " ".join(slur)
    pos_w = " ".join(pho_pos_in_note)
    score_duration_w = " ".join(score_duration)
    f0_path_w = f0_path + name + ".npy"
    real_duration_w = " ".join([str(int(float(i) / 0.0125)) for i in real_duration])
    numpho_w = " ".join(num)

    return '|'.join([wav_path_w, phone_w, pitchid_w, slur_w, pos_w, score_duration_w, f0_path_w, real_duration_w, numpho_w])


def label2list_visinger(label_path, output_path, scp, wav_path="", f0_path=""):
    """
    将一个目录下的所有label文件，按照scp，转化为visinger用的list文件
    """
    f = open(output_path, "w")

    for name in tqdm(scp):
        line = label2line_visinger(os.path.join(label_path, name + ".lab"), wav_path, f0_path)
        f.write(line + "\n")
    f.flush()
    f.close()

def parseLabelFile_fuxi(label_path, out_path):
    """
    从 txt 解析伏羲的 label 格式 \n
    格式: \n
    wav文件名 | 句子文本 | 音素（空格隔开）| 音高 | 曲谱音符时长 | 音素时长 | 连音/转音 | 音素在音节中的位置
    """
    assert os.path.isfile(label_path) and label_path.endswith(".txt"), (
        "label path seems to be wrong: " + label_path
    )

    if not os.path.isdir(out_path):
        os.mkdir(out_path)

    f = open(label_path, "r")
    lines = f.readlines()

    for index in tqdm(range(len(lines))):
        line = lines[index].split("|")
        name = line[0]
        phone = line[2].split(" ")
        pitch = line[3].split(" ")
        score_duration = line[4].split(" ")
        real_duration = line[5].split(" ")
        slur = line[7].split(" ")
        pho_pos_in_note = line[8].split(" ")
        num = get_num_from_pos(pho_pos_in_note)
        labelTools.write_label(os.path.join(out_path, name + ".lab"), phone, pitch, slur, pho_pos_in_note, num, score_duration, real_duration)


def parseLabelFile_fuxi_no_pos(label_path, out_path):
    """
    从 txt 解析伏羲的 label 格式 \n
    格式: \n
    wav文件名 | 句子文本 | 音素（空格隔开）| 音高 | 曲谱音符时长 | 音素时长 | 连音/转音
    """
    assert os.path.isfile(label_path) and label_path.endswith(".txt"), (
        "label path seems to be wrong: " + label_path
    )

    if not os.path.isdir(out_path):
        os.mkdir(out_path)

    f = open(label_path, "r")
    lines = f.readlines()

    for index in tqdm(range(len(lines))):
        line = lines[index].split("|")
        name = line[0]
        phone = line[2].split(" ")
        pitch = line[3].split(" ")
        score_duration = line[4].split(" ")
        real_duration = line[5].split(" ")
        slur = line[6].split(" ")
        labelTools.write_label(os.path.join(out_path, name + ".lab"), [phone, pitch, slur, score_duration, real_duration])


def changePitch(pitch):
    '''
    更改pitch表示
    '''
    pitch_new = []
    for i in pitch:
        i = i.replace("A#", "A#/Bb")
        i = i.replace("C#", "C#/Db")
        i = i.replace("D#", "D#/Eb")
        i = i.replace("F#", "F#/Gb")
        i = i.replace("G#", "G#/Ab")
        pitch_new.append(i)
    return pitch_new


def down_pitch(pitch):
    '''
    给pitch list降一个调
    '''
    pitch_new = []

    for i in pitch:
        if i == "rest":
            pitch_new.append(i)
            continue
        elif len(i) == 2:
            level = int(i[-1])
        elif len(i) == 6:
            level = int(i[-1])
        else:
            print("error pitch:{}".format(i))
            exit(0)
        
        if level > 3:
            level -= 1
        pitch_new.append(i[:-1] + str(level))

    return pitch_new



def add_pos_num_to_labels(in_dir, ref_dir, out_dir): 
    '''
    将 ref_label_dir 下所有 label 的pos, num 的信息，拼接到 in_label_dir 中每个 label 中
    '''

    labels = glob.glob(in_dir + "/*.lab")
    labels.sort()
    in_label = []
    for label in labels:
        phone, pitch, slur, score_duration, real_duration = labelTools.read_label(label)
        in_label.append([os.path.basename(label), phone, pitch, slur, score_duration, real_duration])

    labels = glob.glob(ref_dir + "/*.lab")
    labels.sort()
    ref_label = []
    for label in labels:
        phone, pitch, slur, pho_pos_in_note, num, score_duration, real_duration = labelTools.read_label(label)
        ref_label.append([os.path.basename(label), phone, pitch, slur, pho_pos_in_note, num, score_duration, real_duration])

    a = [len(in_label), len(ref_label)]
    
    assert len(list(set(a))) == 1, "label num is differrent" + str(a)

    if not os.path.isdir(out_dir):
        os.mkdir(out_dir)

    for i in tqdm(range(len(in_label))):
        a_in = in_label[i]
        a_ref = ref_label[i]

        name = a_in[0]
        phone = a_in[1]
        pitch = a_in[2]
        slur = a_in[3]
        pho_pos_in_note = a_ref[4]
        num = a_ref[5]
        score_duration = a_in[4]
        real_duration = a_in[5]
        labelTools.write_label(os.path.join(out_dir, name), phone, pitch, slur, pho_pos_in_note, num, score_duration, real_duration)
    

def fix_TTSlabel_prosody(in_dir, out_dir, old_prosody, new_prosody):
    '''
    修改 tts 中的 #old 到 #new， 并写入 out_dir
    '''
    labels = glob.glob(in_dir + "/*.lab")
    labels.sort()

    if not os.path.isdir(out_dir):
        os.mkdir(out_dir)

    in_label = []
    for label in tqdm(labels):
        phone, tone, seg_tag, prosodies = labelTools.read_label(label)
        new_prosodies = []

        for p in prosodies:
            p = new_prosody if p == old_prosody else p
            new_prosodies.append(p)
        
        out_path = os.path.join(out_dir, os.path.basename(label))
        labelTools.write_label(out_path, [phone, tone, seg_tag, new_prosodies])
        


def midi_parser(midi_fname):
    midi_data = pretty_midi.PrettyMIDI(midi_fname)
    min_time = 0
    try:
        max_time = midi_data.instruments[0].notes[-1].end
    except:
        return None, None
    note_list = []
    dur_in_list = []
    iter_max = 0
    for note in midi_data.instruments[0].notes:
        #try:
            if round(note.start, 6) < iter_max:
                iter_min = iter_max
            else:
                iter_min = round(note.start, 6)
            iter_max = round(note.end, 6)
            if iter_min != iter_max:
                note_item = [iter_min, iter_max, pretty_midi.note_number_to_name(note.pitch)]
                dur_in_item = [iter_min, iter_max, '%.6f' % (note.duration)]
                note_list.append(note_item)
                dur_in_list.append(dur_in_item)
        #except:
        #    print('{}, {}, {}'.format(note.start, note.end, pretty_midi.note_number_to_name(note.pitch)))
    return note_list, dur_in_list
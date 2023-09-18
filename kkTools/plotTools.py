import os
import numpy as np
from tqdm import tqdm
import xlwt
import wave
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from . import wavTools


def plot_mel(mel_path, out_dir):
    mel = np.load(mel_path)
    out_name = 'mel_{}.jpg'.format(os.path.splitext(os.path.basename(mel_path))[0])

    fig = plt.figure(figsize=(10, 2))
    plt.imshow(mel, origin='lower')
    plt.tight_layout()
    plt.savefig(out_name, format='png')
    plt.close()

    fig.savefig(os.path.join(out_dir, out_name))


def plot_pitch(pitch_path):

    fig, ax1 = plt.subplots(figsize=(10, 10), nrows=1)

    pitch = np.load(pitch_path)

    sns.heatmap(pd.DataFrame(np.round(pitch, 2)), annot=True, square=True, cmap="YlGnBu", ax=ax1)
    ax1.set_title('picth', fontsize=18)
    fig.savefig('pitch_{}.jpg'.format(os.path.splitext(os.path.basename(pitch_path))[0]))


def plot_multi_pitch(wav_paths, out_path, labels, sr=16000, hop_size=200, use_lf0=False):
    '''
    画 pitch 折线图，多个线在一张图上
    '''
    import matplotlib
    matplotlib.use('agg')
    for index, wav_path in enumerate(wav_paths):
        f0 = wavTools.extract_pitch_use_harvest(wav_path, sr, hop_size, use_lf0)
        x = np.asarray([i for i in range(f0.shape[0])])
        plt.plot(x, f0, label=labels[index])
    plt.legend(loc='upper right', bbox_to_anchor=(1.05, 1))
    plt.xlabel('Frame')  
    plt.ylabel('Frequency(Hz)')
    # plt.show()
    plt.savefig(out_path)
    
def plot_multifig_pitch(wav_paths, out_path, labels, fmax=700, durs=None, sr=16000, hop_size=200, use_lf0=False):
    '''
    画 pitch 折线图，可以加时长竖线（可选）(输入时长竖线对应第几帧)（2d list）
    '''
    
    import matplotlib
    from matplotlib.gridspec import GridSpec
    matplotlib.use('agg')
    fig = plt.figure(dpi=100,
                 constrained_layout=True,#类似于tight_layout，使得各子图之间的距离自动调整【类似excel中行宽根据内容自适应】
                figsize=(6*len(wav_paths), 6)
                )
    gs = GridSpec(1, len(wav_paths), figure=fig)
    for index, wav_path in enumerate(wav_paths):
        ax = fig.add_subplot(gs[0, index:index+1])
        f0 = wavTools.extract_pitch_use_harvest(wav_path, sr, hop_size, use_lf0)
        # print(np.std(f0))
        # continue
        x = np.asarray([i for i in range(f0.shape[0])])
        ax.set_aspect(f0.shape[0]/fmax)
        plt.ylim(0,fmax)
        plt.plot(x, f0)
        plt.title(labels[index])
        if durs is not None:
            ax.vlines(durs[index], 0, fmax, linestyles='dashed', colors='red')
        # plt.plot(x, f0, label=labels[index])
        # plt.legend(loc='upper right', bbox_to_anchor=(1.05, 1))
        plt.xlabel('Frame')  
        plt.ylabel('Frequency(Hz)')
    # plt.show()
    plt.savefig(out_path)

def plot_pitch_mel(pitch, mel, outfile):

    plt.cla()
    plt.imshow(mel, origin='lower')
    # plt.tight_layout()
    x = np.asarray([i for i in range(pitch.shape[0])])
    pitch = pitch/ 8
    plt.plot(x, pitch, 'red')    
    plt.savefig(outfile)


def main():

    mode = 0

    if mode == 0:
        pitch_path = "/home/work_nfs5_ssd/hzli/data/db6/pitches/db6_emotion_surprise_241609.npy"
        mel_path = "/home/work_nfs5_ssd/hzli/data/db6/mels/db6_emotion_surprise_241609.npy"
        plot_pitch_mel(pitch_path, mel_path)
    if mode == 1:
        mel_path = "/home/work_nfs5_ssd/hzli/kkcode/tmp/tmp_ppg/1.npy"
        out_dir = "/home/work_nfs5_ssd/hzli/kkcode/tmp/tmp_fig"
        plot_mel(mel_path, out_dir)
    if mode == 2:
        wav_dirs = ['/home/work_nfs5_ssd/hzli/acoustic_model/nice_new/log_event_transfer/adavits_db6/db6_test_base_spk5_90w',
                    '/home/work_nfs5_ssd/hzli/acoustic_model/nice_new/log_event_transfer/event-v1_3/20w_0_spk5_90w',
                    '/home/work_nfs5_ssd/hzli/acoustic_model/nice_new/log_event_transfer/event-v4_10_kl0.001/20w_0_base_spk5_90w',
                    '/home/work_nfs5_ssd/hzli/acoustic_model/nice_new/log_event_transfer/event-v4_5_kl0.001/20w_0_base_spk5_90w']
        out_path = "/home/work_nfs5_ssd/hzli/kkcode/tmp/tmp_fig/f0.png"
        utt = "F03-M84-0313070207"
        wav_paths = [os.path.join(d, f"{utt}.wav") for d in wav_dirs]
        labels = ['baseline', 'tp', 'tp-gst', 'proposed']
        plot_multi_pitch(wav_paths, out_path, labels)



if __name__ == "__main__":
    main()
import os
from tqdm import tqdm
import traceback
import numpy as np

from . import scpTools, wavTools

def calc_square_error(np1, np2):
    """
    计算 pitch 的 平方差之和
    输入为两个 np 对象
    返回平方差之和以及长度（两个np的长度要求一致）
    """
    assert np1.shape[0]==np2.shape[0], "length: {}, {}".format(np1.shape[0], np2.shape[0])
    sq = 0
    # print(np1.shape[0], np2.shape[0])

    for index in range(np1.shape[0]):
        sq += (np1[index] - np2[index]) ** 2
    
    return sq, len

def calc_square_error_2(np1, np2):
    """
    计算 pitch 的 平方差之和
    输入为两个 np 对象
    返回平方差之和以及长度（两个np的较小长度）
    """
    minlen = min(np1.shape[0], np2.shape[0])
    np1 = np1[:minlen]
    np2 = np2[:minlen]
    sq = 0
    # print(np1.shape[0], np2.shape[0])

    for index in range(minlen):
        sq += (np1[index] - np2[index]) ** 2
    
    return sq, minlen


def calc_RMSE(dir1, dir2, utts=None):
    '''
    计算两个路径下所有np的RMSE
    '''
    if utts is None:
        utts = [(os.path.basename(path)) for path in os.listdir(dir2)]
        utts.sort()

    num = 0
    error = 0

    for utt in tqdm(utts):
        try:
            f_1 = os.path.join(dir1, utt + ".npy")
            f_2 = os.path.join(dir2, utt + ".npy")

            if not os.path.isfile(f_1):
                print(f_1 + " not exist")
                continue

            tmp1 , tmp2 = calc_square_error(
                    np.load(f_1),
                    np.load(f_2)
                )
            error += tmp1
            num += tmp2
            # print((tmp1 / tmp2) ** 0.5)

        except Exception as e:
            print("\nsome error occured, the related info is as fellows")
            print(utt)
            traceback.print_exc()
            break
        
    return (error / num) ** 0.5


def calc_dur_acc(np_1, np_2):
    '''
    acc = 1 - [++abs(predict(i) - real(i)) / ++max(predict(i), real(i))]
    '''
    fenzi = np.sum(np.abs(np_1 - np_2))
    fenmu = np.sum(np.max(np.stack([np_1, np_2], dim = 0), axis = 0))
    acc = 1 - (fenzi / fenmu)
    return acc


def calc_mse(np_1, np_2):
    return np.sum((np_1 - np_2)**2) / np_1.size

def calc_rmse(np_1, np_2):
    return (np.sum((np_1 - np_2)**2) / np_1.size) ** 0.5

def calc_mae(np_1, np_2):
    return np.sum(np.absolute(np_1 - np_2)) / np_1.size

def calc_corr(np_1, np_2):
    '''
    计算两个向量之间的相关性
    '''
    return np.corrcoef(np_1, np_2)


def calc_pesq(fake_wav_dir, real_wav_dir, utts=None, mode='wb', sample_rate=16000, hop_size=200, win_size=800):
    '''
    调用 torchmetrics 计算 pesq, 越高越好，−0.5 ∼ 4.5，PESQ 值越高则表明被测试的语音具有越好的听觉语音质量 \n
    mode: \n
    wb: wide bond 16k \n
    nb: narrow bond 8k
    '''
    import torch
    from torchaudio.transforms import Resample
    from torchmetrics.audio import PerceptualEvaluationSpeechQuality
    
    assert mode in ("wb", "nb")
    fs = 16000 if mode == "wb" else 8000
    resample = Resample(sample_rate, fs)
    pesq = PerceptualEvaluationSpeechQuality(fs, mode)
    
    if utts is None:
        utts = scpTools.genscp_in_list(fake_wav_dir)
    
    result = []
    for utt in tqdm(utts):
        fake_wav = torch.from_numpy(
            wavTools.load_wav(
                os.path.join(fake_wav_dir, f'{utt}.wav'),
                target_sr=sample_rate,
                win_size=win_size,
                hop_size=hop_size,
            ),
        ).float()
        real_wav = torch.from_numpy(
            wavTools.load_wav(
                os.path.join(real_wav_dir, f'{utt}.wav'),
                target_sr=sample_rate,
                win_size=win_size,
                hop_size=hop_size,
            ),
        ).float()
        fake_wav = fake_wav[:min(fake_wav.size(0), real_wav.size(0))]
        real_wav = real_wav[:min(fake_wav.size(0), real_wav.size(0))]
        result.append(pesq(resample(fake_wav), resample(real_wav)))
    return result


def calc_stoi(fake_wav_dir, real_wav_dir, utts=None, sample_rate=16000, hop_size=200, win_size=800):
    '''
    调用 torchmetrics 计算 stoi，越高越好，0 ∼ 1 中，代表单词被正确理解的百分比，数值取1 时表示语音能够被充分理解 \n
    '''
    import torch
    from torchmetrics.audio import ShortTimeObjectiveIntelligibility

    stoi = ShortTimeObjectiveIntelligibility(sample_rate)
    
    if utts is None:
        utts = scpTools.genscp_in_list(fake_wav_dir)
    
    result = []
    for utt in tqdm(utts):
        fake_wav = torch.from_numpy(
            wavTools.load_wav(
                os.path.join(fake_wav_dir, f'{utt}.wav'),
                target_sr=sample_rate,
                win_size=win_size,
                hop_size=hop_size,
            ),
        ).float()
        real_wav = torch.from_numpy(
            wavTools.load_wav(
                os.path.join(real_wav_dir, f'{utt}.wav'),
                target_sr=sample_rate,
                win_size=win_size,
                hop_size=hop_size,
            ),
        ).float()
        fake_wav = fake_wav[:min(fake_wav.size(0), real_wav.size(0))]
        real_wav = real_wav[:min(fake_wav.size(0), real_wav.size(0))]
        result.append(stoi(fake_wav, real_wav))
    return result


def main():

    mode = 3

    if mode == 0:
        dir1 = "/home/work_nfs5_ssd/hzli/data/fuxi_opensource_2/test/pitch/"
        dir2 = "/home/work_nfs5_ssd/hzli/logdir/syn_M_last/pitch/"
        calc_RMSE(dir1, dir2)
    elif mode == 1:
        from . import scpTools
        in_dir_1 = "/home/work_nfs5_ssd/hzli/kkcode/tmp/real_mels"
        in_dir_2 = "/home/work_nfs5_ssd/hzli/kkcode/tmp/fake_mels"
        utts = scpTools.genscp_in_list(in_dir_1)
        for utt in utts:
            print(utt)
            print(calc_mse(np.load(os.path.join(in_dir_1, f"{utt}.npy")), np.load(os.path.join(in_dir_2, f"{utt}.npy"))))
 


if __name__ == "__main__":
    main()

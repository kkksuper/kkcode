import math
import os
from tqdm import tqdm
import traceback
import numpy as np
import torch
from torchaudio.transforms import Resample
from torchmetrics.audio import PerceptualEvaluationSpeechQuality
from torchmetrics.audio import ShortTimeObjectiveIntelligibility
from typing import List, Literal, Union
import pyworld

from . import scpTools, wavTools, multiTask

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


class PESQ:
    '''
    调用 torchmetrics 计算 pesq, 越高越好，−0.5 ∼ 4.5，PESQ 值越高则表明被测试的语音具有越好的听觉语音质量 \n
    mode: \n
    wb: wide bond 16k \n
    nb: narrow bond 8k
    '''
    def __init__(self, mode='wb', sample_rate=16000, device='cpu') -> None:
        assert mode in ("wb", "nb")
        fs = 16000 if mode == "wb" else 8000
        self.sample_rate = sample_rate
        self.resample = Resample(sample_rate, fs).to(device)
        self.pesq = PerceptualEvaluationSpeechQuality(fs, mode)
        self.device = device
        
        
    def calc(self, fake_wav_path, real_wav_path):
        '''
        返回两个 wav 的 pesq (float) 
        '''
        fake_wav = torch.from_numpy(
            wavTools.load_wav(
                fake_wav_path,
                target_sr=self.sample_rate,
                padding=False
            ),
        ).float()
        real_wav = torch.from_numpy(
            wavTools.load_wav(
                real_wav_path,
                target_sr=self.sample_rate,
                padding=False
            ),
        ).float()
        fake_wav = fake_wav[:min(fake_wav.size(0), real_wav.size(0))].to(self.device)
        real_wav = real_wav[:min(fake_wav.size(0), real_wav.size(0))].to(self.device)
        return self.pesq(self.resample(fake_wav), self.resample(real_wav))
    
    
    def run(self, fake_wav_dir, real_wav_dir, utts=None, use_tqdm=True, numthread=1) -> List[float] :
        '''
        返回每个 utt 的 pesq，顺序和输入 utts 一样 
        '''
        if utts is None:
            utts = scpTools.genscp_in_list(fake_wav_dir)
        
        if numthread > 1:
            inputs = [
                {
                    "fake_wav_path": os.path.join(fake_wav_dir, f'{utt}.wav'),
                    "real_wav_path": os.path.join(real_wav_dir, f'{utt}.wav')
                } for utt in utts
            ]
            if self.device == torch.device('cpu') or self.device == 'cpu':
                result = multiTask.multiThread_use_ProcessPoolExecutor_dicitem_dicarg(inputs, numthread, self.calc, {}, use_tqdm)
            else:
                result = multiTask.multiThread_use_multiprocessing_dicitem_dicarg_spawn(inputs, numthread, self.calc, {}, use_tqdm)
        else: 
            result = []
            for utt in tqdm(utts) if use_tqdm else utts:
                result.append(self.calc(os.path.join(fake_wav_dir, f'{utt}.wav'), os.path.join(real_wav_dir, f'{utt}.wav')))
                
        return result
    

class STOI:
    '''
    调用 torchmetrics 计算 stoi，越高越好，0 ∼ 1 中，代表单词被正确理解的百分比，数值取1 时表示语音能够被充分理解 \n
    '''
    def __init__(self, sample_rate=16000, device='cpu') -> None:
        self.sample_rate = sample_rate
        self.stoi = ShortTimeObjectiveIntelligibility(sample_rate)
        self.device = device
        
        
    def calc(self, fake_wav_path, real_wav_path):
        '''
        返回两个 wav 的 pesq (float) 
        '''
        fake_wav = torch.from_numpy(
            wavTools.load_wav(
                fake_wav_path,
                target_sr=self.sample_rate,
                padding=False
            ),
        ).float()
        real_wav = torch.from_numpy(
            wavTools.load_wav(
                real_wav_path,
                target_sr=self.sample_rate,
                padding=False
            ),
        ).float()
        fake_wav = fake_wav[:min(fake_wav.size(0), real_wav.size(0))].to(self.device)
        real_wav = real_wav[:min(fake_wav.size(0), real_wav.size(0))].to(self.device)
        return self.stoi(fake_wav, real_wav)
    
    
    def run(self, fake_wav_dir, real_wav_dir, utts=None, use_tqdm=True, numthread=1) -> List[float] :
        '''
        返回每个 utt 的 stoi，顺序和输入 utts 一样 
        '''
        if utts is None:
            utts = scpTools.genscp_in_list(fake_wav_dir)
        
        if numthread > 1:
            inputs = [
                {
                    "fake_wav_path": os.path.join(fake_wav_dir, f'{utt}.wav'),
                    "real_wav_path": os.path.join(real_wav_dir, f'{utt}.wav')
                } for utt in utts
            ]
            if self.device == torch.device('cpu') or self.device == 'cpu':
                result = multiTask.multiThread_use_ProcessPoolExecutor_dicitem_dicarg(inputs, numthread, self.calc, {}, use_tqdm)
            else:
                result = multiTask.multiThread_use_multiprocessing_dicitem_dicarg_spawn(inputs, numthread, self.calc, {}, use_tqdm)
        else: 
            result = []
            for utt in tqdm(utts) if use_tqdm else utts:
                result.append(self.calc(os.path.join(fake_wav_dir, f'{utt}.wav'), os.path.join(real_wav_dir, f'{utt}.wav')))
                
        return result

class MCD:
    '''
    计算 MCD（mel cepstral distortion），越低越好\n
    reference repo: https://github.com/chenqi008/pymcd/blob/main/pymcd/mcd.py
    '''
    def __init__(self, sample_rate=16000, mode:Literal['plain', 'dtw', 'dtw_sl']='plain', FRAME_PERIOD=5.0, device='cpu') -> None:
        self.sample_rate = sample_rate
        self.log_spec_dB_const = 10.0 / math.log(10.0) * math.sqrt(2.0) # 6.141851463713754
        self.mode = mode
        self.FRAME_PERIOD = FRAME_PERIOD
        self.device = device
    
    # distance metric
    def log_spec_dB_dist(self, x, y):
        # log_spec_dB_const = 10.0 / math.log(10.0) * math.sqrt(2.0)
        diff = x - y
        return self.log_spec_dB_const * math.sqrt(np.inner(diff, diff))
    
    # calculate distance (metric)
    # def calculate_mcd_distance(self, x, y, distance, path):
    def calculate_mcd_distance(self, x, y, path):
        '''
        param path: pairs between x and y
        '''
        pathx = list(map(lambda l: l[0], path))
        pathy = list(map(lambda l: l[1], path))
        x, y = x[pathx], y[pathy]
        frames_tot = x.shape[0]       # length of pairs

        z = x - y
        min_cost_tot = np.sqrt((z * z).sum(-1)).sum()

        return frames_tot, min_cost_tot
    
    # extract acoustic features
    # alpha = 0.65  # commonly used at 22050 Hz
    def wav2mcep_numpy(self, loaded_wav, alpha=0.65, fft_size=512):
        import pysptk

        # Use WORLD vocoder to spectral envelope
        _, sp, _ = pyworld.wav2world(loaded_wav.astype(np.double), fs=self.sample_rate,
                                       frame_period=self.FRAME_PERIOD, fft_size=fft_size)

        # Extract MCEP features
        mcep = pysptk.sptk.mcep(sp, order=13, alpha=alpha, maxiter=0,
                               etype=1, eps=1.0E-8, min_det=0.0, itype=3)

        return mcep
        
    def calc(self, fake_wav_path, real_wav_path):
        '''
        返回两个 wav 的 MCD (float) 
        '''
        fake_wav = wavTools.load_wav(
                fake_wav_path,
                target_sr=self.sample_rate,
                padding=False
        )
        real_wav = wavTools.load_wav(
                real_wav_path,
                target_sr=self.sample_rate,
                padding=False
        )
        
        if self.mode == 'plain':
            if len(real_wav)<len(fake_wav):
                real_wav = np.pad(real_wav, (0, len(fake_wav)-len(real_wav)))
            else:
                fake_wav = np.pad(fake_wav, (0, len(real_wav)-len(fake_wav)))
        
        fake_mcep = self.wav2mcep_numpy(fake_wav)
        real_mcep = self.wav2mcep_numpy(real_wav)
        
        if self.mode == "plain":
            # print("Calculate plain MCD ...")
            path = []
            # for i in range(num_temp):
            for i in range(len(real_mcep)):
                path.append((i, i))
        elif self.mode == "dtw":
            # print("Calculate MCD-dtw ...")
            from fastdtw import fastdtw
            from scipy.spatial.distance import euclidean
            _, path = fastdtw(real_mcep[:, 1:], fake_mcep[:, 1:], dist=euclidean)
        elif self.mode == "dtw_sl":
            # print("Calculate MCD-dtw-sl ...")
            from fastdtw import fastdtw
            from scipy.spatial.distance import euclidean
            cof = len(real_mcep)/len(fake_mcep) if len(real_mcep)>len(fake_mcep) else len(fake_mcep)/len(real_mcep)
            _, path = fastdtw(real_mcep[:, 1:], fake_mcep[:, 1:], dist=euclidean)

        frames_tot, min_cost_tot = self.calculate_mcd_distance(real_mcep, fake_mcep, path)

        if self.mode == "dtw_sl":
            mean_mcd = cof * self.log_spec_dB_const * min_cost_tot / frames_tot
        else:
            mean_mcd = self.log_spec_dB_const * min_cost_tot / frames_tot

        return mean_mcd
    
    
    def run(self, fake_wav_dir, real_wav_dir, utts=None, use_tqdm=True, numthread=1) -> List[float] :
        '''
        返回每个 utt 的 MCD，顺序和输入 utts 一样 
        '''
        if utts is None:
            utts = scpTools.genscp_in_list(fake_wav_dir)
        
        if numthread > 1:
            inputs = [
                {
                    "fake_wav_path": os.path.join(fake_wav_dir, f'{utt}.wav'),
                    "real_wav_path": os.path.join(real_wav_dir, f'{utt}.wav')
                } for utt in utts
            ]
            if self.device == torch.device('cpu') or self.device == 'cpu':
                result = multiTask.multiThread_use_ProcessPoolExecutor_dicitem_dicarg(inputs, numthread, self.calc, {}, use_tqdm)
            else:
                result = multiTask.multiThread_use_multiprocessing_dicitem_dicarg_spawn(inputs, numthread, self.calc, {}, use_tqdm)
        else: 
            result = []
            for utt in tqdm(utts) if use_tqdm else utts:
                result.append(self.calc(os.path.join(fake_wav_dir, f'{utt}.wav'), os.path.join(real_wav_dir, f'{utt}.wav')))
                
        return result


class SpeechMOS:
    '''
    调用 utmos, 计算 speech mos \n
    reference repo: https://github.com/tarepan/SpeechMOS
    '''
    def __init__(self, sample_rate=16000, device='cpu') -> None:
        self.sample_rate = sample_rate
        self.utmos = torch.hub.load(repo_or_dir="tarepan/SpeechMOS:v1.2.0", model='utmos22_strong', trust_repo=True)
        self.utmos.eval()
        self.device = device
        self.utmos.to(device)
        
        
    def calc(self, wav_path):
        '''
        返回 wav 的 SpeechMOS (float) 
        '''
        wav = torch.from_numpy(
            wavTools.load_wav(
                wav_path,
                target_sr=self.sample_rate,
                padding=False
            ),
        ).float().to(self.device).unsqueeze(0)
        with torch.no_grad():
            res = self.utmos(wav, self.sample_rate)
        return res
    
    
    def run(self, wav_dir, utts=None, use_tqdm=True, numthread=1) -> List[float] :
        '''
        返回每个 utt 的 SpeechMOS，顺序和输入 utts 一样 
        '''
        if utts is None:
            utts = scpTools.genscp_in_list(wav_dir)
        
        if numthread > 1:
            inputs = [
                {
                    "wav_path": os.path.join(wav_dir, f'{utt}.wav'),
                } for utt in utts
            ]
            if self.device == torch.device('cpu') or self.device == 'cpu':
                result = multiTask.multiThread_use_ProcessPoolExecutor_dicitem_dicarg(inputs, numthread, self.calc, {}, use_tqdm)
            else:
                result = multiTask.multiThread_use_multiprocessing_dicitem_dicarg_spawn(inputs, numthread, self.calc, {}, use_tqdm)
        else: 
            result = []
            for utt in tqdm(utts) if use_tqdm else utts:
                result.append(self.calc(os.path.join(wav_dir, f'{utt}.wav')))
                
        return result
    

class WespeakerCalc:
    '''
    调用 wespeaker, 提取声纹表征，并计算相似度
    reference repo: https://github.com/wenet-e2e/wespeaker
    '''
    def __init__(self, device='cpu', language:Literal['english', 'chinese']='chinese') -> None:
        import wespeaker
        self.model = wespeaker.load_model(language)
        self.model.set_device(device)
        self.device = device
        
        
    def calc(self, fake_wav_path, real_wav_path):
        '''
        返回两个 wav 的 wespeaker embedding 的 cosine similarity (float) 
        '''
        
        fake_emb = self.model.extract_embedding(fake_wav_path)
        real_emb = self.model.extract_embedding(real_wav_path)
        
        cos_simi = np.dot(fake_emb, real_emb) / (np.linalg.norm(fake_emb) * np.linalg.norm(real_emb)).tolist()
        
        return cos_simi
    
    def extract_embedding(self, wav_path):
        '''
        返回 wav 的 wespeaker embedding
        '''
        return self.model.extract_embedding(wav_path)
    
    
    def run(self, fake_wav_dir, real_wav_dir, utts=None, use_tqdm=True, numthread=1) -> List[float] :
        '''
        返回每个 utt 的 speaker cosine similarity，顺序和输入 utts 一样 
        fake dir 必须是 wav 文件夹，real dir 可以是 wav 文件夹或者单个 wav 文件，如果是单个 wav 文件，那么所有的 fake wav 都会和这个 real wav 进行比较，否则，每个 fake wav 会和文件名对应的 real wav 进行比较
        '''
        if utts is None:
            utts = scpTools.genscp_in_list(fake_wav_dir)
        
        if numthread > 1:
            inputs = [
                {
                    "fake_wav_path": os.path.join(fake_wav_dir, f'{utt}.wav'),
                    "real_wav_path": os.path.join(real_wav_dir, f'{utt}.wav') if os.path.isdir(real_wav_dir) else real_wav_dir
                } for utt in utts
            ]
            if self.device == torch.device('cpu') or self.device == 'cpu':
                result = multiTask.multiThread_use_ProcessPoolExecutor_dicitem_dicarg(inputs, numthread, self.calc, {}, use_tqdm)
            else:
                result = multiTask.multiThread_use_multiprocessing_dicitem_dicarg_spawn(inputs, numthread, self.calc, {}, use_tqdm)
        else: 
            result = []
            for utt in tqdm(utts) if use_tqdm else utts:
                result.append(self.calc(os.path.join(fake_wav_dir, f'{utt}.wav'), os.path.join(real_wav_dir, f'{utt}.wav') if os.path.isdir(real_wav_dir) else real_wav_dir))
                
        return result


class WER:
    def __init__(self,
                 metrics: Union['wer', 'cer'] = 'wer',
                 language: Union['en', 'zh'] = 'en'):
        '''
        the wer/cer evaluation of the model is based on the whisper model, supporting both chinese and english.
        '''
        import whisper
        from torchmetrics.text import CharErrorRate, WordErrorRate
        self.model = whisper.load_model("large", download_root='/apdcephfs_cq10/share_1297902/user/shaanyang/interns/hanzhaoli/workspace/cache/open_model/whisper')
        self.metrics_name = metrics
        self.metrics = WordErrorRate() if metrics == 'wer' else CharErrorRate()
        self.language = language
        
        if torch.cuda.is_available():
            device = torch.device("cuda")
            self.model = self.model.to(device)
            self.metrics = self.metrics.to(device)
            
            
    def filter_func(self, string: str) -> str:
        '''
        filter function for text to remove punctuation and lower case, to exclude the influence of punctuation and case
        '''
        string = string.replace(".", "")
        string = string.replace("'", "")
        string = string.replace("-", "")
        string = string.replace(",", "")
        string = string.replace("!", "")
        string = string.replace('"', '')
        string = string.replace("?", "")
        string = string.replace(":", "")
        string = string.replace(";", "")
        string = string.replace("*", "")
        string = string.replace("  ", " ")
        string = string.lower()
        return string    
    
    
    def run_item(self, ref_item, pred_item, mode: Union['gt_audio', 'gt_content'] = 'gt_content'):
        '''
        input:
            ref_item: reference item. If mode is 'gt_audio', it should be audio path. If mode is 'gt_content', it should be content string
            pred_item: prediction item. the audio path.
            mode: 'gt_audio' or 'gt_content'. 'gt_audio' means the ref_item is audio path, and the
        output:
            score: wer score
            content_pred: predicted content
            content_gt: ground truth content
        '''
        if mode == "gt_audio":
            content_gt = self.model.transcribe(ref_item, verbose=False, language=self.language)["text"]
        elif mode == "gt_content":
            content_gt = ref_item
        else:
            raise ValueError(f"mode {mode} is not supported")

        content_pred = self.model.transcribe(pred_item, verbose=False, language=self.language)["text"]

        content_gt = self.filter_func(content_gt)
        content_pred = self.filter_func(content_pred)
        
        return self.metrics(content_pred, content_gt).detach().cpu().numpy().tolist(), content_pred, content_gt
        
        
    def run(self, ref_items, pred_items, mode: Union['gt_audio', 'gt_content'] = 'gt_content', print_res=True):
        '''
        input:
            ref_items: list of reference items. If mode is 'gt_audio', it should be list of audio paths. If mode is 'gt_content', it should be list of content strings
            pred_items: list of prediction items. the audio paths.
            mode: 'gt_audio' or 'gt_content'. 'gt_audio' means the ref_items are audio paths, and the content will be transcribed by the model. 'gt_content' means the ref_items are already content strings.
            print_res: whether to print the result
        output:
            scores: list of wer scores
            utt2content: dict of utt2content, including content_gt, content_pred, and score
        '''
        scores = []
        utt2content = {}
        
        pbar = tqdm(range(len(ref_items)), desc=f'calc {self.metrics_name}', leave=False, dynamic_ncols=True)
        
        for i in pbar:
            ref_item = ref_items[i]
            pred_item = pred_items[i]
            score, content_pred, content_gt = self.run_item(ref_item, pred_item, mode)
            scores.append(score)
            utt2content[scpTools.get_basename(pred_item)] = {
                'content_gt': content_gt,
                'content_pred': content_pred,
                'score': score
            }
        
        if print_res:
            cost_time = pbar.format_dict['elapsed']
            avg_time = round(cost_time / len(scores), 2)
            print(f'total {len(scores)} items, cost time: {cost_time} s, avg time: {avg_time} item/s, avg score: {np.mean(scores)}')
            
        return scores, utt2content


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

import os
from tqdm import tqdm
import traceback
import numpy as np
from . import scpTools

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

    print((error / num) ** 0.5)
    return (error / num) ** 0.5


def calc_dur_acc(np_1, np_2):
    '''
    经过重构，可能有问题，使用时注意
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


def main():

    mode = 3

    if mode == 0:
        dir1 = "/home/work_nfs5_ssd/hzli/data/fuxi_opensource_2/test/pitch/"
        dir2 = "/home/work_nfs5_ssd/hzli/logdir/syn_M_last/pitch/"
        calc_RMSE(dir1, dir2)
    elif mode == 1:
        in_dir_1 = "/home/work_nfs5_ssd/hzli/kkcode/tmp/real_mels"
        in_dir_2 = "/home/work_nfs5_ssd/hzli/kkcode/tmp/fake_mels"
        utts = scpTools.genscp_in_list(in_dir_1)
        for utt in utts:
            print(utt)
            print(calc_mse(np.load(os.path.join(in_dir_1, f"{utt}.npy")), np.load(os.path.join(in_dir_2, f"{utt}.npy"))))
 


if __name__ == "__main__":
    main()

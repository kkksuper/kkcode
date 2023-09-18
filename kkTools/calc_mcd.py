import argparse
from numpy.linalg import norm
from numpy import array, zeros, full, argmin, inf, ndim
import audio
from scipy.spatial.distance import cdist
from tqdm import tqdm
import numpy as np
import argparse
import os

class DTWAligner:
    def __init__(self, predict_list, target_dict, predict_dir, target_dir,args,hparams):
        self.predict_acoustics = {}
        self.target_acoustics = {}
        self.args = args
        self.hparams= hparams
        if args.datatype == "mel":
            for predict_id in predict_list:
                self.predict_acoustics[predict_id] = (np.load(os.path.join(predict_dir, predict_id)) + 1.0) / 2.0
                self.target_acoustics[predict_id] = (np.load(os.path.join(target_dir, target_dict[predict_id])) + 1.0) / 2.0
                
                # min_len = min(self.predict_acoustics[predict_id].shape[0], self.target_acoustics[predict_id].shape[0])
                # self.predict_acoustics[predict_id] = self.predict_acoustics[predict_id][:min_len]
                # self.target_acoustics[predict_id] = self.target_acoustics[predict_id][:min_len]
                # self.predict_acoustics[predict_id] = np.load(os.path.join(predict_dir, predict_id))
                # self.target_acoustics[predict_id] = np.load(os.path.join(target_dir, target_dict[predict_id]))
            
        elif args.datatype == "bark":
            minmax = np.load(self.args.minmax_path)
            mins = minmax["bark_min"]
            maxs = minmax["bark_max"]
            min_value = -1 * self.hparams.max_abs_value \
                if self.hparams.symmetric_acoustic else 0
            for predict_id in predict_list:
                 predict_data=np.load(os.path.join(predict_dir, predict_id))
                 target_data=np.load(os.path.join(target_dir, target_dict[predict_id]))
                 predict_data = audio._normalize_min_max(predict_data, maxs, mins, self.hparams.max_abs_value, min_value)
                 self.predict_acoustics[predict_id] =(predict_data[:,:30]  + 4.0) / 8.0
                 self.target_acoustics[predict_id] =(target_data[:,:30] + 4.0) / 8.0
        else:
            raise NotImplementedError(
                "The  data type {} is not implemented.".format(args.datatype))

    def __call__(self):
        aligned_predicts = {}
        aligned_targets = {}
        for key in tqdm(self.predict_acoustics):
            dist, cost, acc_cost, path = accelerated_dtw(self.predict_acoustics[key], 
                                                         self.target_acoustics[key], 
                                                         dist=lambda x, y: norm(x - y, ord=1))

            path = np.array(path)
            aligned_predicts[key] = self.predict_acoustics[key][path[0]]
            aligned_targets[key] = self.target_acoustics[key][path[1]]
            assert aligned_predicts[key].shape == aligned_targets[key].shape
        return aligned_predicts, aligned_targets

def calculate_mcd(predicts, targets):
    utt_mcd = {}
    logSpecDbConst = 10.0 / np.log(10.0) * np.sqrt(2.0)
    for key in tqdm(predicts):
        predict = predicts[key]
        target = targets[key]
        diff_sum = 0.0
        for i in range(predict.shape[0]):
            diff = predict[i,:] - target[i,:]
            diff_sum += logSpecDbConst * np.sqrt(np.dot(diff, diff))
        utt_mcd[key] = diff_sum / predict.shape[0]

    total_mcd = 0.0
    for key in utt_mcd:
        total_mcd += utt_mcd[key]
    return utt_mcd, total_mcd / len(utt_mcd)


def accelerated_dtw(x, y, dist, warp=1):
    """
    Computes Dynamic Time Warping (DTW) of two sequences in a faster way.
    Instead of iterating through each element and calculating each distance,
    this uses the cdist function from scipy (https://docs.scipy.org/doc/scipy/reference/generated/scipy.spatial.distance.cdist.html)

    :param array x: N1*M array
    :param array y: N2*M array
    :param string or func dist: distance parameter for cdist. When string is given, cdist uses optimized functions for the distance metrics.
    If a string is passed, the distance function can be 'braycurtis', 'canberra', 'chebyshev', 'cityblock', 'correlation', 'cosine', 'dice', 'euclidean', 'hamming', 'jaccard', 'kulsinski', 'mahalanobis', 'matching', 'minkowski', 'rogerstanimoto', 'russellrao', 'seuclidean', 'sokalmichener', 'sokalsneath', 'sqeuclidean', 'wminkowski', 'yule'.
    :param int warp: how many shifts are computed.
    Returns the minimum distance, the cost matrix, the accumulated cost matrix, and the wrap path.
    """
    assert len(x)
    assert len(y)
    if ndim(x) == 1:
        x = x.reshape(-1, 1)
    if ndim(y) == 1:
        y = y.reshape(-1, 1)
    r, c = len(x), len(y)
    D0 = zeros((r + 1, c + 1))
    D0[0, 1:] = inf
    D0[1:, 0] = inf
    D1 = D0[1:, 1:]
    D0[1:, 1:] = cdist(x, y, dist)
    C = D1.copy()
    for i in range(r):
        for j in range(c):
            min_list = [D0[i, j]]
            for k in range(1, warp + 1):
                min_list += [D0[min(i + k, r), j],
                             D0[i, min(j + k, c)]]
            D1[i, j] += min(min_list)
    if len(x) == 1:
        path = zeros(len(y)), range(len(y))
    elif len(y) == 1:
        path = range(len(x)), zeros(len(x))
    else:
        path = _traceback(D0)
    return D1[-1, -1] / sum(D1.shape), C, D1, path


def _traceback(D):
    i, j = array(D.shape) - 2
    p, q = [i], [j]
    while (i > 0) or (j > 0):
        tb = argmin((D[i, j], D[i, j + 1], D[i + 1, j]))
        if tb == 0:
            i -= 1
            j -= 1
        elif tb == 1:
            i -= 1
        else:  # (tb == 2):
            j -= 1
        p.insert(0, i)
        q.insert(0, j)
    return array(p), array(q)

def integrity_test(args):
    # Check whether configurations exists or being defined correctly
    if not os.path.exists(args.predict_acoustic_dir):
        raise IOError(
            'Predicted acoustic path {} is empty.'.format(args.predict_acoustic_dir))

    if not os.path.exists(args.target_acoustic_dir):
        raise IOError(
            'Target acoustic path {} is empty.'.format(args.target_acoustic_dir))

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--predict_acoustic_dir', 
                        required=True,
                        help='folder to contain predicted acoustic spectrograms')
    parser.add_argument('--target_acoustic_dir', 
                        required=True,
                        help='folder to contain ground-truth acoustic spectrograms')
    parser.add_argument('--scp_dir', 
                        required=True,
                        help='folder to contain scp')
    parser.add_argument('--datatype',
                        default="mel",
                        help='mel or bark')
    parser.add_argument('--minmax_path',
                        default=None,
                        help='full path to minmax.npz file')

    args = parser.parse_args()

    hparams = {
        "preprocess_type": "AcousticProcessor",
        "max_abs_value": 1,
        "symmetric_acoustic": True,
        "sample_rate":22050,
        "hop_size": 256,
        "win_size": 1024,
        "fmax": 11025,
        "rescale": False,
        "trim_silence": False
    }

    integrity_test(args)

    scp = open(args.scp_dir, "r").readlines()
    scp = [i.strip() for i in scp]

    predict_acoustic_files = [fp for fp in os.listdir(args.predict_acoustic_dir) if fp.endswith('.npy') and os.path.splitext(fp)[0][:10] in scp]

    all_target_files = os.listdir(args.target_acoustic_dir)
    target_acoustic_files = {}
    for acoustic_file in predict_acoustic_files:
        # predict acoustic name is not equal to target acoustic
        target_file = os.path.splitext(acoustic_file)[0] + '.npy'
        if not target_file in all_target_files:
            raise ValueError(
                'Target acoustic file {} not exists.'.format(target_file))
        else:
            target_acoustic_files[acoustic_file] = target_file

    # Dynamic time wrapping
    aligner = DTWAligner(predict_acoustic_files, target_acoustic_files, 
        args.predict_acoustic_dir, args.target_acoustic_dir, args, hparams)
    aligned_predicts, aligned_targets = aligner()

    utt_mcd, average_mcd = calculate_mcd(aligned_predicts, aligned_targets)
    print("workdir: {} , {}".format(args.predict_acoustic_dir, args.target_acoustic_dir))
    print('MCD: {}'.format(average_mcd))


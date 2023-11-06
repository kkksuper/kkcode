import multiprocessing
from concurrent.futures import ProcessPoolExecutor
from functools import partial
from tqdm import tqdm

def multiThread_use_multiprocessing_multiarg(scp, numthread, func, *args):
    '''
    根据scp得到要处理的文件名单, 创建numthread个线程, 调用func函数, 并传入若干参数以及该线程要处理的scp \n
    Parameters: \n
        scp - 要处理的文件名list
        numthread - 线程数 \n
        func - 调用的函数, 该函数会接收到两部分参数, scp和args \n
        args - 传入任意个参数, 执行函数最终会收到一个args参数元组 \n
    '''
    lens = len(scp)
    len_per_thread = lens // (numthread - 1)

    print("lens:{}, threads num:{}, per thread len:{}".format(lens, numthread, len_per_thread))

    for index in range(numthread):

        start_index = len_per_thread * index
        end_index = len_per_thread * (index + 1)
        end_index = end_index if index!=numthread-1 else lens + 1
        cur_scp = scp[start_index : end_index]
        # print("thread", index, ": ", start_index, ",", end_index-1)
        tmp = multiprocessing.Process(target=func, args=(cur_scp, args))
        tmp.start()


def multiThread_use_multiprocessing_dicarg_spawn(scp, numthread, func, args, use_tqdm=True):
    '''
    根据scp得到要处理的文件名单, 创建numthread个线程, 调用func函数, 并传入若干参数以及该线程要处理的scp \n
    共享显卡 \n
    Parameters: \n
        scp - 要处理的文件名list \n
        numthread - 线程数 \n
        func - 调用的函数, 该函数会接收到两部分参数, 一个文件名和args \n
        args - 传入的一个字典参数, 执行函数最终会收到多个参数 \n
    '''
    import torch.multiprocessing
    ctx = torch.multiprocessing.get_context("spawn")
    pool = ctx.Pool(numthread)
    pool_list = []
    
    tqdmbar= tqdm(total=len(scp))
    update = lambda *tmp: tqdmbar.update()

    for item in scp:
        res = pool.apply_async(partial(func, item, **args), callback=update if use_tqdm else None)
        pool_list.append(res)
    
    pool.close()  # 关闭进程池，不再接受新的进程
    pool.join()  # 主进程阻塞等待子进程的退出

    return [i.get() for i in pool_list]


def multiThread_use_multiprocessing_dicitem_dicarg_spawn(scp, numthread, func, args, use_tqdm=True):
    '''
    根据scp得到要处理的名单(字典数组), 创建numthread个线程, 调用func函数, 并传入若干参数以及该线程要处理的scp \n
    共享显卡 \n
    Parameters: \n
        scp - 要处理的文件名list \n
        numthread - 线程数 \n
        func - 调用的函数, 该函数会接收到两部分参数, 一个文件名和args \n
        args - 传入的一个字典参数, 执行函数最终会收到多个参数 \n
    '''
    import torch.multiprocessing
    ctx = torch.multiprocessing.get_context("spawn")
    pool = ctx.Pool(numthread)
    pool_list = []
    
    if use_tqdm:
        tqdmbar= tqdm(total=len(scp))
        update = lambda *tmp: tqdmbar.update()

    for item in scp:
        res = pool.apply_async(partial(func, **item, **args), callback=update if use_tqdm else None)
        pool_list.append(res)
    
    pool.close()  # 关闭进程池，不再接受新的进程
    pool.join()  # 主进程阻塞等待子进程的退出

    return [i.get() for i in pool_list]


def multiThread_use_ProcessPoolExecutor_dicarg(scp, numthread, func, args, use_tqdm=True, use_valid=False):
    '''
    根据scp得到要处理的文件名单, 创建numthread个线程, 调用func函数, 并传入若干参数以及该线程要处理的scp \n
    Parameters: \n
        scp - 要处理的文件名list \n
        numthread - 线程数 \n
        func - 调用的函数, 该函数会接收到两部分参数, 一个文件名和args \n
        args - 传入的一个字典参数, 执行函数最终会收到多个参数 \n
    '''
    executor = ProcessPoolExecutor(max_workers=numthread)
    results = []
    if use_valid:
        valid = executor.submit(partial(func, scp[0], **args))
        valid.result()
    for item in scp:
        results.append(executor.submit(partial(func, item, **args)))
    if use_tqdm:
        return [result.result() for result in tqdm(results)]
    else:
        return [result.result() for result in results]
    
    
def multiThread_use_ProcessPoolExecutor_dicitem_dicarg(scp, numthread, func, args, use_tqdm=True, use_valid=False):
    '''
    根据scp得到要处理的名单(字典数组), 创建numthread个线程, 调用func函数, 并传入若干参数以及该线程要处理的scp \n
    Parameters: \n
        scp - 要处理的文件名list \n
        numthread - 线程数 \n
        func - 调用的函数, 该函数会接收到两部分参数, 一个文件名和args \n
        args - 传入的一个字典参数, 执行函数最终会收到多个参数 \n
    '''
    executor = ProcessPoolExecutor(max_workers=numthread)
    results = []
    if use_valid:
        valid = executor.submit(partial(func, **scp[0], **args))
        valid.result()
    for item in scp:
        results.append(executor.submit(partial(func, **item, **args)))
    if use_tqdm:
        return [result.result() for result in tqdm(results)]
    else:
        return [result.result() for result in results]


def multiThread_use_ProcessPoolExecutor_multiarg(scp, numthread, func, use_tqdm=True, use_valid=False, *args):
    '''
    根据scp得到要处理的文件名单, 创建numthread个线程, 调用func函数, 并传入若干参数以及该线程要处理的scp \n
    Parameters: \n
        scp - 要处理的文件名list \n
        numthread - 线程数 \n
        func - 调用的函数, 该函数会接收到两部分参数, 一个文件名和args \n
        args - 传入任意个参数, 执行函数最终会收到一个args参数元组 \n
    '''
    executor = ProcessPoolExecutor(max_workers=numthread)
    results = []
    if use_valid:
        valid = executor.submit(partial(func, scp[0], **args))
        valid.result()
    for item in scp:
        results.append(executor.submit(partial(func, item, args)))
    if use_tqdm:
        return [result.result() for result in tqdm(results)]
    else:
        return [result.result() for result in results]


def test_use_multiarg(item, args):
    print(f"item: {item}, args0: {args[0]}, args1: {args[1]}")
    return item

import time
import random
def test_use_dicarg(item, a=1, b=2, c=3):
    # print(f"item: {item}, a: {a}, b: {b}, c: {c}")
    time.sleep(random.random()*10)
    return item

def test_use_dicitem_dicarg(a=1, b=2, c=3):
    print(f"a: {a}, b: {b}, c: {c}")
    time.sleep(random.random()*1)
    return a

def main():

    mode = 3

    if mode == 1:
        dir1 = "/home/work_nfs5_ssd/hzli/kkcode/py"
        ex = "ex1"
        utts = [f'items {i}' for i in range(40)]
        multiThread_use_multiprocessing_multiarg(utts, 8, test_use_multiarg, dir1, ex)
    elif mode == 2:
        dir1 = "/home/work_nfs5_ssd/hzli/kkcode/py"
        ex = {"a":"18", "b":"20"}
        utts = [i for i in range(40)]
        results = multiThread_use_ProcessPoolExecutor_dicarg(utts, 20, test_use_dicarg, ex)
        print(results)
    elif mode == 3:
        dir1 = "/home/work_nfs5_ssd/hzli/kkcode/py"
        ex = {"c":"20"}
        utts = [{"a": i, "b": i*2} for i in range(40)]
        results = multiThread_use_ProcessPoolExecutor_dicitem_dicarg(utts, 20, test_use_dicitem_dicarg, ex)
        print(results)


if __name__ == "__main__":
    main()
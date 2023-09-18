import json
from operator import itemgetter


def merge_jsons(file_list, outpath):
    '''
    将 file_list 中的所有文件内容合并，输出至outpath
    '''
    js = {}
    for file in file_list:
        f = open(file, 'r')
        new_js = json.load(f)
        for key in new_js:
            if key in js:
                js[key] += new_js[key]
            else:
                js[key] = new_js[key]
    save_json(js, outpath)


def sort_json_1(js, reverse=True):
    '''
    按照json键值名排序(从小到大), reverse 表示逆转排序,
    '''
    new_js = sorted(js.items(), key=lambda d: d[1], reverse=reverse)
    new_js = {i[0]:i[1] for i in new_js}
    return new_js


def sort_json_2(js, attr, reverse=True):
    '''
    对json数组, 按照json的某个键的值排序(从小到大), reverse 表示逆转排序
    '''
    new_js = sorted(js, key=itemgetter(attr), reverse=reverse)
    new_js = {i[0]:i[1] for i in new_js}
    return new_js


def sort_json_3(js, reverse=True):
    '''
    按照json的键排序(从小到大), reverse 表示逆转排序
    '''
    f = zip(js.keys(), js.values())
    c = sorted(f, reverse=reverse, key=lambda l:l[1])
    new_js = {}
    for cc in c:
        new_js[cc[0]] = cc[1]
    return new_js

def read_json(js_path, enc='utf-8'):
    '''
    根据 json 路径，读取
    '''
    f = open(js_path, 'r', encoding=enc)
    js = json.load(f)
    return js

def save_json(js, out_dir, enc='utf-8'):
    '''
    将json转为字符串，输出到文件
    '''
    js = json.dumps(js, ensure_ascii=False)
    f = open(out_dir, 'w', encoding=enc)
    f.write(js)
    f.flush()
    f.close()


def main():

    mode = 6

    if mode == 0:
        print("some utils")
    elif mode == 1:
        save_json({
            "我的": 23,
            32: 43
        }, "/home/work_nfs5_ssd/hzli/kkcode/tmp/test.json")


if __name__ == "__main__":
    main()
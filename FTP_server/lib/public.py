#!/usr/bin/env python
# -*- coding:utf8 -*-
# __author__ = 'glh'

import hashlib
import os


def create_md5(salt, content):
    md5_obj = hashlib.md5(salt.encode('utf-8'))
    md5_obj.update(content.encode('utf-8'))
    return md5_obj.hexdigest()


def get_all_file_md5(path):
    file_size = os.path.getsize(path)
    md5_obj = hashlib.md5()
    with open(path, 'rb') as f:
        while file_size:
            date = f.read(1024)
            md5_obj.update(date)
            file_size -= len(date)
        return md5_obj.hexdigest()


if __name__ == '__main__':
    print(create_md5('goulonghui', '123456'))
    print(get_all_file_md5(r'D:\python_test\22常用模块2\1 钻石继承.py'))


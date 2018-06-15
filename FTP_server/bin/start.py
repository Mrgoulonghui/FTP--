#!/usr/bin/env python
# -*- coding:utf8 -*-
# __author__ = 'glh'

import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

from core import main


if __name__ == '__main__':
    cmd = input('开启服务器请输入start:')
    main.OpenServer(cmd)


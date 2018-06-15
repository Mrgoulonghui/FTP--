#!/usr/bin/env python
# -*- coding:utf8 -*-
# __author__ = 'glh'

import socketserver
from conf import settings
from core import server


class OpenServer:
    def __init__(self, cmd):
        self.cmd = cmd
        if hasattr(self, cmd):
            func = getattr(self, cmd)
            func()
        else:
            print('\033[1;31m傻啊你，叫你输入start,不听话,还不重启服务器\033[0m')

    @staticmethod
    def start():
        print('服务器已启动！')
        s = socketserver.ThreadingTCPServer(settings.IP_PORT, server.MyServer)
        s.serve_forever()


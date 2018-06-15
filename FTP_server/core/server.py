#!/usr/bin/env python
# -*- coding:utf8 -*-
# __author__ = 'glh'

import socketserver
import json
import os
from conf import settings
from lib import public


class MyServer(socketserver.BaseRequestHandler):
    def handle(self):
        while True:
            data = self.recv_dic_data()
            if data.get('action'):
                if hasattr(self, data.get('action')):
                    func = getattr(self, data.get('action'))
                    func(data)

    def recv_dic_data(self):
        data = self.request.recv(settings.BUFFER_SIZE)
        return json.loads(data.decode('utf-8'))

    def send_dic_data(self, data):
        self.request.send(json.dumps(data).encode('utf-8'))

    def register(self, data):
        # dic_data = {'action': 'register', 'username': username, 'password': password}
        username = data.get('username')
        password = data.get('password')
        _password = public.create_md5(username, password)
        path = os.path.join(settings.BASE_DIR, 'db', 'user_info')
        with open(path, 'r+', encoding='utf-8') as f:
            for line in f:
                if line:
                    user_name = line.split('|')[0].strip()
                    if username == user_name:
                        self.request.send('123'.encode('utf-8'))
                        return username
            f.write(f'{username}|{_password}\n')
            user_path = os.path.join(settings.BASE_DIR, 'user_home', username)
            os.chdir(os.path.dirname(user_path))
            os.mkdir(username)
            self.request.send('456'.encode('utf-8'))

    def login(self, data):
        # dic_data = {'action': 'register', 'username': username, 'password': password}
        username = data.get('username')
        password = data.get('password')
        _password = public.create_md5(username, password)
        path = os.path.join(settings.BASE_DIR, 'db', 'user_info')
        with open(path, 'r+', encoding='utf-8') as f:
            for line in f:
                if line:
                    user_name, pass_word = line.split('|')
                    if username == user_name.strip() and _password == pass_word.strip():
                        self.request.send('456'.encode('utf-8'))
                        self.user = username
                        self.main_path = os.path.join(settings.BASE_DIR, 'user_home', username)
                        return username
            self.request.send('123'.encode('utf-8'))

    def upload(self, data):
        file_name = data.get('file_name')
        file_size = data.get('file_size')
        target_path = data.get('target_path')
        target_abs_path = os.path.join(self.main_path, target_path, file_name)

        has_received = 0
        if os.path.exists(target_abs_path):
            file_has_size = os.path.getsize(target_abs_path)
            if file_has_size < file_size:
                # 断点续传
                self.request.send('800'.encode('utf-8'))
                client_choice = self.request.recv(settings.BUFFER_SIZE).decode('utf-8')
                if client_choice == 'Y':
                    file_has_size_dic = {'file_has_size': file_has_size}
                    self.send_dic_data(file_has_size_dic)
                    has_received += file_has_size
                    f = open(target_abs_path, 'ab')
                else:
                    # 选择为N,不续传,直接覆盖
                    f = open(target_abs_path, 'wb')

            else:
                # 文件存在，需要校验一致性
                self.request.send('801'.encode('utf-8'))

                client_md5mm = self.request.recv(settings.BUFFER_SIZE).decode('utf-8')
                serve_md5mm = public.get_all_file_md5(target_abs_path)
                if client_md5mm == serve_md5mm:
                    self.request.send('456'.encode('utf-8'))  # 校验通过，发一个456，
                else:
                    # 校验不通过，直接打开文件，覆盖
                    f = open(target_abs_path, 'wb')

        else:
            # 文件不存在
            self.request.send('802'.encode('utf-8'))
            f = open(target_abs_path, 'wb')

        while has_received < file_size:
            data = self.request.recv(settings.BUFFER_SIZE)
            f.write(data)
            has_received += len(data)
        f.close()
        # 校验文件的一致性
        client_md5mm = self.request.recv(settings.BUFFER_SIZE).decode('utf-8')
        serve_md5mm = public.get_all_file_md5(target_abs_path)
        if client_md5mm == serve_md5mm:
            self.request.send('456'.encode('utf-8'))  # 校验通过，发一个456，
        else:
            self.request.send('123'.encode('utf-8'))  # 校验不通过，发一个123，

    def download(self, data):
        file_name = data.get('file_name')
        target_path = data.get('target_path')
        target_abs_path = os.path.join(self.main_path, target_path, file_name)

        has_send = 0
        if os.path.exists(target_abs_path):
            file_size = os.path.getsize(target_abs_path)
            self.request.send(str(file_size).encode('utf-8'))  # 先把文件大小发给客户端
            data_dic = self.recv_dic_data()  # 接收到客户端发来的状态 800，801，802
            if data_dic.get('status') == 800:
                # 断点续传
                file_has_size = data_dic.get('file_has_size')
                has_send += file_has_size
            elif data_dic.get('status') == 801:
                # 文件存在，需要校验一致性
                client_md5mm = self.request.recv(settings.BUFFER_SIZE).decode('utf-8')
                serve_md5mm = public.get_all_file_md5(target_abs_path)
                if client_md5mm == serve_md5mm:
                    self.request.send('456'.encode('utf-8'))  # 校验通过，发一个456，
            # elif data_dic.get('status') == 802:
            #     # 文件不存在,直接发，不用写
            #     pass

            with open(target_abs_path, 'rb') as f:
                f.seek(has_send)
                while has_send < file_size:
                    data = f.read(1024)
                    self.request.send(data)
                    has_send += len(data)
            # 校验文件的一致性
            client_md5mm = self.request.recv(settings.BUFFER_SIZE).decode('utf-8')
            serve_md5mm = public.get_all_file_md5(target_abs_path)
            if client_md5mm == serve_md5mm:
                self.request.send('456'.encode('utf-8'))  # 校验通过，发一个456，
            else:
                self.request.send('123'.encode('utf-8'))  # 校验不通过，发一个123，
        else:
            self.request.send('None'.encode('utf-8'))

    def dir(self, data):
        file_list = os.listdir(self.main_path)
        self.send_dic_data(file_list)

    def cd(self, data):
        target_path = data.get('target_path')
        if target_path == '..'and os.path.basename(self.main_path) != self.user:
            self.main_path = os.path.dirname(self.main_path)
        elif target_path == '.':
            pass
        # else:
        #     # 权限不够
        #     self.request.send('456'.encode('utf-8'))
        #     return
        elif target_path in os.listdir(self.main_path):
            self.main_path = os.path.join(self.main_path, target_path)
        else:
            # 文件夹不存在,权限不够
            self.request.send('123'.encode('utf-8'))
            return
        self.request.send(self.main_path.encode('utf-8'))

    def mkdir(self, data):
        want_create_directory = data.get('want_create_directory')
        abs_path = os.path.join(self.main_path, want_create_directory)
        if want_create_directory not in os.listdir(abs_path):
            if '/' in want_create_directory:
                os.makedirs(want_create_directory)
            else:
                os.mkdir(want_create_directory)
            self.request.send('456'.encode('uft-8'))
        else:
            self.request.send('123'.encode('utf-8'))

















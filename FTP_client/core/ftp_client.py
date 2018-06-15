#!/usr/bin/env python
# -*- coding:utf8 -*-
# __author__ = 'glh'

import socket
import json
import os
import sys
from conf import settings
from lib import public


class MyClient:
    def __init__(self):
        self.sk = None
        self.user = None
        self.current = None
        self.main_path = settings.BASE_DIR
        self.get_ip_port()
        self.show_choice()

    def get_ip_port(self):
        ip = input('请输入要连接地服务器ip:').strip()
        port = input('请输入要连接地端口port:').strip()
        try:
            if 0 < int(port) < 65535:
                ip_port = (ip, int(port))
                self.make_connect(ip_port)
        except Exception as e:
            exit(e)

    def make_connect(self, ip_port):
        self.sk = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sk.connect(ip_port)
        print('\033[1;32m连接成功\033[0m')

    def send_dic_message(self, data):
        self.sk.send(json.dumps(data).encode('utf-8'))

    def recv_dic_data(self):
        data = self.sk.recv(settings.BUFFER_SIZE)
        return json.loads(data.decode('utf-8'))

    def register(self):
        while 1:
            username = input('请输入用户名/q退出：').strip()
            if username.lower() == 'q': self.quit()
            password = input('请输入密码/q退出  ：').strip()
            if password.lower() == 'q': self.quit()
            password_ = input('请确认密码/q退出  ：').strip()
            if password_.lower() == 'q': self.quit()
            if password == password_:
                dic_data = {'action': 'register', 'username': username, 'password': password}
                self.send_dic_message(dic_data)
                if self.sk.recv(1024).decode('utf-8') == '456':
                    print('注册成功,请登录使用')
                    user_path = os.path.join(settings.BASE_DIR, 'db', username)
                    os.chdir(os.path.dirname(user_path))
                    os.mkdir(username)
                    self.show_choice()
                    return True
                else:
                    print('用户名已经存在,重新选择')
            else:
                print('\033[1;31m两次密码输入不一致,重新输入\033[0m')

    def login(self):
        while 1:
            username = input('请输入用户名/q退出)：').strip()
            if username.lower() == 'q': self.quit()
            password = input('请输入密码 /q退出 ：').strip()
            if password.lower() == 'q': self.quit()
            dic_data = {'action': 'login', 'username': username, 'password': password}
            self.send_dic_message(dic_data)
            if self.sk.recv(1024).decode('utf-8') == '456':
                self.user = username
                self.current = username
                print('登陆成功')
                while 1:
                    self.run()
            else:
                print('用户名或者密码错误,请重新输入')

    def quit(self):
        self.sk.close()
        exit()

    def show_choice(self):
        print('''
        1, 注册
        2，登陆
        3，退出
        ''')
        dic_choice = {'1': 'register', '2': 'login', '3': 'quit'}
        choice = input('请输入你的选择/q退出：').strip()
        if choice == 'q': self.quit()
        if choice in dic_choice:
            if hasattr(self, dic_choice.get(choice)):
                func = getattr(self, dic_choice.get(choice))
                func()

    def run(self):
        print('\033[1;32m请输入的命令,以空格分开/q退出\033[0m')
        cmd = input(f'当前目录为\033[1;34m{[self.current]}\033[0m：').strip()
        if cmd.lower() == 'q': self.quit()
        cmd_list = cmd.split()
        if hasattr(self, cmd_list[0].strip()):
            func = getattr(self, cmd_list[0].strip())
            func(cmd_list)
        else:
            print('命令有误')

    def upload(self, cmd_list):
        # 命令输入  upload 本地自己目录下的文件名 上传到服务端自己目录下的那个文件夹
        action, local_path, target_path = cmd_list
        client_path = os.path.join(self.main_path, 'db', self.user, local_path)
        file_name = os.path.basename(client_path)
        file_size = os.path.getsize(client_path)
        data = {'action': action, 'file_name': file_name, 'file_size': file_size, 'target_path': target_path}
        self.send_dic_message(data)

        result = self.sk.recv(settings.BUFFER_SIZE).decode('utf-8')  # 接收数字 800，801，802
        has_send = 0
        if result == '800':
            # 断点续传
            while 1:
                choice = input('文件已经存在，但是不完整，是否要接着上一次继续上传Y/N？q退出').strip()
                if choice.lower() == 'q': self.quit()
                if choice.upper() == 'Y':
                    # 断点续传
                    self.sk.send('Y'.encode('utf-8'))
                    file_has_size = self.recv_dic_data()
                    has_send += file_has_size.get('file_has_size')
                    break
                elif choice.upper() == 'N':
                    # 不续传，直接覆盖
                    self.sk.send('N'.encode('utf-8'))
                else:
                    print('命令错误')
        elif result == '801':
            # 文件存在，需要校验一致性
            md5_mm = public.get_all_file_md5(client_path)
            self.sk.send(md5_mm.encode('utf-8'))
            msg_num = self.sk.recv(settings.BUFFER_SIZE).decode('utf-8')
            if msg_num == '456':
                print('\033[1;34m上传成功!\033[0m')
                return
            # else: pass 文件不一致直接清空重写
        # elif result == '802':
        #     # 文件不存在，直接发,直接打开文件，不用写逻辑
        #     pass

        f = open(client_path, 'rb')
        f.seek(has_send)
        while has_send < file_size:
            data = f.read(1024)
            self.sk.send(data)
            has_send += len(data)
            self.show_process(has_send, file_size)
        f.close()
        # 全部上传完毕，校验文件的一致性
        md5_mm = public.get_all_file_md5(client_path)
        self.sk.send(md5_mm.encode('utf-8'))
        msg_num = self.sk.recv(settings.BUFFER_SIZE).decode('utf-8')
        if msg_num == '456':
            print('\033[1;34m上传成功!\033[0m')
        else:
            print('\033[1;34m上传失败，请重试!\033[0m')

    def download(self, cmd_list):
        # downlad, file_name, target_path
        action, local_path, target_path = cmd_list
        client_path = os.path.join(self.main_path, 'db', self.user, local_path)
        file_name = os.path.basename(client_path)
        data = {'action': action, 'file_name': file_name, 'target_path': target_path}

        self.send_dic_message(data)

        res = self.sk.recv(settings.BUFFER_SIZE).decode('utf-8')
        if res == 'None':
            print('\033[1;31m该资源不存在\033[0m')
        else:
            file_size = int(res)
            has_received = 0
            if os.path.exists(client_path):
                file_has_size = os.path.getsize(client_path)
                if file_has_size < file_size:
                    # 断点续传
                    choice = input('文件已经存在，但是不完整，是否要接着上一次继续下载Y/N？q退出').strip()
                    if choice.lower() == 'q': self.quit()
                    elif choice.upper() == 'Y':
                        data_dic = {'status': 800, 'file_has_size': file_has_size}
                        self.send_dic_message(data_dic)  # 告诉服务端我要断点续传和我的文件大小
                        has_received += file_has_size
                        f = open(client_path, 'ab')
                    else:
                        f = open(client_path, 'wb')
                else:
                    # 文件存在，需要校验一致性
                    data_dic = {'status': 802}
                    self.send_dic_message(data_dic)

                    md5_mm = public.get_all_file_md5(client_path)
                    self.sk.send(md5_mm.encode('utf-8'))
                    msg_num = self.sk.recv(settings.BUFFER_SIZE).decode('utf-8')
                    if msg_num == '456':
                        print('\033[1;34m下载成功!\033[0m')
                    else:
                        # 校验不通过，
                        f = open(client_path, 'wb')
            else:
                # 文件不存在，直接写
                data_dic = {'status': 802}
                self.send_dic_message(data_dic)
                f = open(client_path, 'wb')

            while has_received < file_size:
                data = self.sk.recv(settings.BUFFER_SIZE)
                f.write(data)
                has_received += len(data)
                self.show_process(has_received, file_size)
            f.close()
            # 全部下载完毕，校验文件的一致性
            md5_mm = public.get_all_file_md5(client_path)
            self.sk.send(md5_mm.encode('utf-8'))
            msg_num = self.sk.recv(settings.BUFFER_SIZE).decode('utf-8')
            if msg_num == '456':
                print('\033[1;34m下载成功!\033[0m')
            else:
                print('\033[1;34m下载失败，请重试!\033[0m')

    @staticmethod
    def show_process(has, total):
        rate = has / total
        rate_num = int(rate * 100)
        sys.stdout.write('\r%s%s%%' % ('*' * (rate_num + 1), rate_num))

    def dir(self, cmd_list):
        # dir
        data = {'action': 'dir'}
        self.send_dic_message(data)

        file_list = self.recv_dic_data()
        if not file_list:
            print('当前文件夹为空')
        for file in file_list:
            print(file)

    def cd(self, cmd_list):
        # cd filename
        action, target_path = cmd_list
        data = {'action': action, 'target_path': target_path}
        self.send_dic_message(data)

        server_res = self.sk.recv(settings.BUFFER_SIZE).decode('utf-8')
        if server_res == '123':
            print('\033[1;31m文件夹不存在,或者到达顶级目录!\033[0m')
        else:
            self.current = os.path.basename(server_res)

    def mkdir(self, cmd_list):
        # mkdir file_name   mkdir file_name/file_name
        action, want_create_directory = cmd_list
        data = {'action': action, 'want_create_directory': want_create_directory}
        self.send_dic_message(data)

        res = self.sk.recv(settings.BUFFER_SIZE).decode('utf-8')
        if res == '123':
            print('该文件夹已经存在！')
        else:
            print('创建成功！')










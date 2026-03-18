import tkinter as tk
import os



class LoginInterceptor:
    @staticmethod
    def check_login():
        # 检查是否存在登录状态文件
        if not os.path.exists('login_status.txt'):
            # 如果不存在，返回False
            return None

        # 如果存在，读取用户信息
        with open('login_status.txt', 'r') as f:
            try:
                user_id = int(f.readline().strip())
                username = f.readline().strip()
                return user_id, username
            except:
                # 如果文件格式错误，删除文件
                os.remove('login_status.txt')
                return None

    @staticmethod
    def save_login_status(user_id, username):
        # 保存登录状态
        with open('login_status.txt', 'w') as f:
            f.write(f"{user_id}\n{username}")

    @staticmethod
    def clear_login_status():
        # 清除登录状态
        if os.path.exists('login_status.txt'):
            os.remove('login_status.txt')
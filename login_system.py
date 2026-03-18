import tkinter as tk
from tkinter import messagebox
import sqlite3
from datetime import datetime
import os
import hashlib
import re
from db_manager import DatabaseManager
from login_interceptor import LoginInterceptor
import logging
from utils import validate_password # 导入密码验证函数



class LoginSystem:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("图像处理系统 - 登录")
        self.root.geometry("400x300")

        # 创建数据库管理器
        self.db = DatabaseManager()

        # 创建登录界面
        self.create_login_widgets()

        # 初始化日志
        self.logger = logging.getLogger()

        # 在 __init__ 或 create_registration_widgets 开头 ...
        self.show_password_var = tk.BooleanVar()
        self.show_confirm_password_var = tk.BooleanVar()

    def create_login_widgets(self):
        # 创建登录框架
        self.login_frame = tk.Frame(self.root)
        self.login_frame.pack(pady=20)

        # 用户名
        tk.Label(self.login_frame, text="用户名:").grid(row=0, column=0, padx=5, pady=5)
        self.username_entry = tk.Entry(self.login_frame)
        self.username_entry.grid(row=0, column=1, padx=5, pady=5)

        # 密码
        tk.Label(self.login_frame, text="密码:").grid(row=1, column=0, padx=5, pady=5)
        self.password_entry = tk.Entry(self.login_frame, show="*")
        self.password_entry.grid(row=1, column=1, padx=5, pady=5)

        # 按钮
        tk.Button(self.login_frame, text="登录",
                  command=self.login).grid(row=2, column=0, padx=5, pady=10)
        tk.Button(self.login_frame, text="注册",
                  command=self.show_register).grid(row=2, column=1, padx=5, pady=10)

    def create_register_widgets(self):
        # 清除登录框架
        self.login_frame.pack_forget()

        # 创建注册框架
        self.register_frame = tk.Frame(self.root)
        self.register_frame.pack(pady=20)

        # 用户名
        tk.Label(self.register_frame, text="用户名:").grid(row=0, column=0, padx=5, pady=5)
        self.reg_username = tk.Entry(self.register_frame)
        self.reg_username.grid(row=0, column=1, padx=5, pady=5)

        # 密码输入
        tk.Label(self.register_frame, text="设置密码:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.reg_password_entry = tk.Entry(self.register_frame)
        self.reg_password_entry.grid(row=2, column=1, padx=5, pady=5)

        self.password_placeholder = "至少8位，含大小写字母、数字和符号"
        self.reg_password_entry.insert(0, self.password_placeholder)
        self.reg_password_entry.config(fg='grey')

        self.reg_password_entry.bind('<FocusIn>', self.on_password_entry_focus_in)
        self.reg_password_entry.bind('<FocusOut>', self.on_password_entry_focus_out)

        # 添加显示密码复选框
        show_pass_check = tk.Checkbutton(self.register_frame, text="显示",
                                         variable=self.show_password_var,
                                         onvalue=True, offvalue=False,
                                         command=self.toggle_password_visibility)
        show_pass_check.grid(row=2, column=2, padx=5, pady=5, sticky="w")

        # 确认密码输入
        tk.Label(self.register_frame, text="确认密码:").grid(row=3, column=0, padx=5, pady=5, sticky="w")
        self.confirm_password_entry = tk.Entry(self.register_frame)
        self.confirm_password_entry.grid(row=3, column=1, padx=5, pady=5)

        self.confirm_placeholder = "再次输入密码"
        self.confirm_password_entry.insert(0, self.confirm_placeholder)
        self.confirm_password_entry.config(fg='grey')

        self.confirm_password_entry.bind('<FocusIn>', self.on_confirm_entry_focus_in)
        self.confirm_password_entry.bind('<FocusOut>', self.on_confirm_entry_focus_out)

        # 添加显示确认密码复选框
        show_confirm_check = tk.Checkbutton(self.register_frame, text="显示",
                                            variable=self.show_confirm_password_var,
                                            onvalue=True, offvalue=False,
                                            command=self.toggle_confirm_password_visibility)
        show_confirm_check.grid(row=3, column=2, padx=5, pady=5, sticky="w")

        # 邮箱
        tk.Label(self.register_frame, text="邮箱:").grid(row=4, column=0, padx=5, pady=5)
        self.reg_email = tk.Entry(self.register_frame)
        self.reg_email.grid(row=4, column=1, padx=5, pady=5)

        # 注册按钮
        tk.Button(self.register_frame, text="注册", command=self.register_user).grid(row=5, column=0, columnspan=1, pady=10)
        tk.Button(self.register_frame, text="返回登录",command=self.back_to_login).grid(row=5, column=1, padx=5, pady=5)

    def show_register(self):
        self.create_register_widgets()

    def back_to_login(self):
        self.register_frame.pack_forget()
        self.login_frame.pack(pady=20)

    def validate_email(self, email):
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None

    def hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()

    # def validate_password(self, password):
    #     """
    #     验证密码复杂度
    #     要求：至少8位，包含大小写字母、数字和特殊符号
    #     """
    #     if len(password) < 8:
    #         return False, "密码长度至少为8位"
    #     if not re.search(r'[A-Z]', password):
    #         return False, "密码必须包含大写字母"
    #     if not re.search(r'[a-z]', password):
    #         return False, "密码必须包含小写字母"
    #     if not re.search(r'\d', password):
    #         return False, "密码必须包含数字"
    #     if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
    #         return False, "密码必须包含特殊符号"
    #     return True, "密码符合要求"

    def register_user(self):
        username = self.reg_username.get()
        # 获取密码时，要检查是否还是占位符状态
        password = self.reg_password_entry.get()
        if password == self.password_placeholder:
            password = "" # 如果是占位符，实际密码为空

        confirm_password = self.confirm_password_entry.get()
        if confirm_password == self.confirm_placeholder:
            confirm_password = "" # 如果是占位符，实际密码为空

        if not username or not password or not confirm_password:
            messagebox.showerror("错误", "请填写所有字段")
            return

        if password != confirm_password:
            messagebox.showerror("错误", "两次输入的密码不一致")
            return

        is_valid, message = validate_password(password)
        if not is_valid:
            messagebox.showerror("密码错误", message)
            return

        if not self.validate_email(self.reg_email.get()):
            messagebox.showerror("错误", "邮箱格式不正确")
            return

        # 检查用户名和邮箱是否已存在
        if self.db.check_username_exists(username):
            messagebox.showerror("错误", "用户名已存在")
            return

        if self.db.check_email_exists(self.reg_email.get()):
            messagebox.showerror("错误", "邮箱已被注册")
            return

        # 添加新用户
        hashed_password = self.hash_password(password)
        if self.db.add_user(username, hashed_password, self.reg_email.get()):
            messagebox.showinfo("成功", "注册成功！")
            self.back_to_login()
        else:
            messagebox.showerror("错误", "注册失败，请稍后重试")

    def login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()

        if not username or not password:
            messagebox.showerror("错误", "请输入用户名和密码")
            return

        try:
            # 记录登录尝试
            self.logger.info(f"用户 {username} 尝试登录")
            
            # 验证用户
            hashed_password = self.hash_password(password)
            user = self.db.check_user(username, hashed_password)

            if user:
                # 更新最后登录时间
                self.db.update_last_login(username)
                # 保存登录状态
                LoginInterceptor.save_login_status(user[0], username)
                # 登录成功，启动主程序
                self.root.destroy()
                self.start_main_program(user[0])
            else:
                messagebox.showerror("错误", "用户名或密码错误")
        except Exception as e:
            self.logger.error(f"登录过程发生错误: {str(e)}", exc_info=True)

    def start_main_program(self, user_id):
        # 不需要创建新的 Tk 实例
        from image_editor import ImageEditor
        root = tk.Tk()  # 只创建一个 Tk 实例
        app = ImageEditor(root)

        # 获取用户名
        conn = self.db.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT username FROM users WHERE user_id=?", (user_id,))
            username = cursor.fetchone()[0]
            # 设置用户信息
            app.set_user(user_id, username)
        finally:
            conn.close()

        root.mainloop()

    def run(self):
        self.root.mainloop()

    # --- 添加事件处理函数 ---
    def on_password_entry_focus_in(self, event):
        """当密码输入框获得焦点时调用"""
        if self.reg_password_entry.get() == self.password_placeholder:
            self.reg_password_entry.delete(0, tk.END)
            self.reg_password_entry.config(fg='black')
            # 根据复选框状态设置初始 show 状态
            if not self.show_password_var.get():
                self.reg_password_entry.config(show='*')
            else:
                self.reg_password_entry.config(show='') # 即使显示，也不是占位符了

    def on_password_entry_focus_out(self, event):
        """当密码输入框失去焦点时调用"""
        if not self.reg_password_entry.get():
            self.reg_password_entry.insert(0, self.password_placeholder)
            self.reg_password_entry.config(fg='grey', show='') # 占位符总是可见的

    def on_confirm_entry_focus_in(self, event):
        """当确认密码输入框获得焦点时调用"""
        if self.confirm_password_entry.get() == self.confirm_placeholder:
            self.confirm_password_entry.delete(0, tk.END)
            self.confirm_password_entry.config(fg='black')
            # 根据复选框状态设置初始 show 状态
            if not self.show_confirm_password_var.get():
                self.confirm_password_entry.config(show='*')
            else:
                self.confirm_password_entry.config(show='')

    def on_confirm_entry_focus_out(self, event):
        """当确认密码输入框失去焦点时调用"""
        if not self.confirm_password_entry.get():
            self.confirm_password_entry.insert(0, self.confirm_placeholder)
            self.confirm_password_entry.config(fg='grey', show='') # 占位符总是可见的

    def toggle_password_visibility(self):
        """切换密码输入框的可见性"""
        current_text = self.reg_password_entry.get()
        if current_text != self.password_placeholder: # 只有在不是占位符时才切换 show
            if self.show_password_var.get(): # 如果复选框被选中 (显示)
                self.reg_password_entry.config(show='')
            else: # 如果复选框未被选中 (隐藏)
                self.reg_password_entry.config(show='*')

    def toggle_confirm_password_visibility(self):
        """切换确认密码输入框的可见性"""
        current_text = self.confirm_password_entry.get()
        if current_text != self.confirm_placeholder: # 只有在不是占位符时才切换 show
            if self.show_confirm_password_var.get(): # 如果复选框被选中 (显示)
                self.confirm_password_entry.config(show='')
            else: # 如果复选框未被选中 (隐藏)
                self.confirm_password_entry.config(show='*')
    # -------------------------

# 如果需要直接运行这个文件，将实例化代码放在这里
if __name__ == "__main__":
    app = LoginSystem()
    app.run()

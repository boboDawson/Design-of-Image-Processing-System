import cv2
import numpy as np
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import os
import sys
import logging
from datetime import datetime


class ImageEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("图像编辑器")

        # 添加窗口关闭事件处理
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # 初始化变量
        self.image = None
        self.photo = None
        self.display_width = 500
        self.display_height = 400
        self.user_id = None  # 用户ID
        self.username = None  # 用户名

        # 裁剪相关变量
        self.crop_start_x = None
        self.crop_start_y = None
        self.crop_end_x = None
        self.crop_end_y = None
        self.is_cropping = False

        # 添加文字相关变量
        self.is_adding_text = False
        self.text_position = None

        # 添加历史记录列表用于保存操作历史
        self.history = []
        self.current_step = -1

        # 添加绘图相关变量
        self.is_drawing = False
        self.last_x = None
        self.last_y = None
        self.draw_color = (0, 0, 255)  # 默认红色
        self.draw_thickness = 2

        # 创建主界面
        self.create_user_panel()  # 添加用户面板
        self.create_widgets()

        self.logger = logging.getLogger()

    def create_user_panel(self):
        # 创建用户信息面板
        self.user_panel = tk.Frame(self.root)
        self.user_panel.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

        # 用户信息标签
        self.user_label = tk.Label(self.user_panel, text="当前用户：未登录")
        self.user_label.pack(side=tk.LEFT, padx=5)

        # 用户操作按钮
        tk.Button(self.user_panel, text="切换用户",
                  command=self.switch_user).pack(side=tk.RIGHT, padx=5)
        tk.Button(self.user_panel, text="退出登录",
                  command=self.logout).pack(side=tk.RIGHT, padx=5)

    def set_user(self, user_id, username):
        """设置当前用户信息"""
        self.user_id = user_id
        self.username = username
        self.user_label.config(text=f"当前用户：{username}")
        self.logger.info(f"图像编辑器启动 - 用户: {username}(ID:{user_id})")

    def switch_user(self):
        """切换用户"""
        if messagebox.askyesno("切换用户", "确定要切换用户吗？"):
            # 显示用户选择对话框
            self.show_user_select_dialog()

    def show_user_select_dialog(self):
        # 创建用户选择对话框
        dialog = tk.Toplevel(self.root)
        dialog.title("选择用户")
        dialog.geometry("300x400")

        # 从数据库获取所有用户
        from db_manager import DatabaseManager
        db = DatabaseManager()
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT username FROM users")
        users = cursor.fetchall()
        conn.close()

        # 创建用户列表框
        listbox = tk.Listbox(dialog, width=30)
        listbox.pack(pady=10, padx=10)

        # 添加用户到列表
        for user in users:
            listbox.insert(tk.END, user[0])

        def select_user():
            selection = listbox.curselection()
            if selection:
                username = listbox.get(selection[0])
                dialog.destroy()
                # 显示登录框
                self.show_login_dialog(username)
        # 添加按钮
        tk.Button(dialog, text="选择", command=select_user).pack(pady=5)
        tk.Button(dialog, text="新用户注册",
                  command=lambda: self.restart_with_registration(dialog)).pack(pady=5)
        tk.Button(dialog, text="取消",
                  command=dialog.destroy).pack(pady=5)

    def show_login_dialog(self, username):
        # 创建登录对话框
        dialog = tk.Toplevel(self.root)
        dialog.title("用户登录")
        dialog.geometry("300x150")

        # 用户名显示
        tk.Label(dialog, text=f"用户名: {username}").pack(pady=5)

        # 密码输入
        tk.Label(dialog, text="密码:").pack(pady=5)
        password_entry = tk.Entry(dialog, show="*")
        password_entry.pack(pady=5)

        def do_login():
            from db_manager import DatabaseManager
            db = DatabaseManager()

            # 验证密码
            hashed_password = self.hash_password(password_entry.get())
            user = db.check_user(username, hashed_password)

            if user:
                db.update_last_login(username)
                dialog.destroy()
                # 更新当前用户信息
                self.set_user(user[0], username)
                messagebox.showinfo("成功", "登录成功！")
            else:
                messagebox.showerror("错误", "密码错误")

        tk.Button(dialog, text="登录", command=do_login).pack(pady=10)

    def hash_password(self, password):
        """密码加密"""
        import hashlib
        return hashlib.sha256(password.encode()).hexdigest()

    def restart_with_registration(self, dialog):
        """重启程序到注册界面"""
        dialog.destroy()
        self.root.quit()
        self.root.destroy()
        python = sys.executable
        os.execl(python, python, "login_system.py")

    def logout(self):
        """退出登录"""
        if messagebox.askyesno("退出登录", "确定要退出登录吗？"):
            # 清除登录状态
            from login_interceptor import LoginInterceptor
            LoginInterceptor.clear_login_status()
            # 重启到登录界面
            self.root.quit()
            self.root.destroy()
            python = sys.executable
            os.execl(python, python, "login_system.py")

    def create_widgets(self):
        # 左侧工具栏
        self.tools_frame = tk.Frame(self.root)
        self.tools_frame.pack(side=tk.LEFT, padx=5, pady=5)

        # 基本操作按钮
        tk.Button(self.tools_frame, text="打开图片", command=self.load_image).pack(pady=2)
        tk.Button(self.tools_frame, text="裁剪图片", command=self.crop_image).pack(pady=2)
        tk.Button(self.tools_frame, text="添加水印", command=self.add_text).pack(pady=2)
        tk.Button(self.tools_frame, text="绘图工具", command=self.draw_mode).pack(pady=2)
        tk.Button(self.tools_frame, text="滤镜效果", command=self.apply_filters).pack(pady=2)
        tk.Button(self.tools_frame, text="调整色阶", command=self.adjust_levels).pack(pady=2)
        tk.Button(self.tools_frame, text="旋转图片", command=self.rotate_image).pack(pady=2)
        tk.Button(self.tools_frame, text="翻转图片", command=self.flip_image).pack(pady=2)
        tk.Button(self.tools_frame, text="保存图片", command=self.save_image).pack(pady=2)

        # 右侧效果按钮
        self.effects_frame = tk.Frame(self.root)
        self.effects_frame.pack(side=tk.RIGHT, padx=5, pady=5)

        tk.Button(self.effects_frame, text="反相效果", command=self.negative_effect).pack(pady=2)
        tk.Button(self.effects_frame, text="黑白效果", command=self.bw_effect).pack(pady=2)
        tk.Button(self.effects_frame, text="风格化", command=self.stylization_effect).pack(pady=2)
        tk.Button(self.effects_frame, text="素描效果", command=self.sketch_effect).pack(pady=2)
        tk.Button(self.effects_frame, text="浮雕效果", command=self.emboss_effect).pack(pady=2)
        tk.Button(self.effects_frame, text="复古效果", command=self.sepia_effect).pack(pady=2)
        tk.Button(self.effects_frame, text="模糊处理", command=self.blur_image).pack(pady=2)
        tk.Button(self.effects_frame, text="二值化", command=self.binary_threshold).pack(pady=2)
        tk.Button(self.effects_frame, text="腐蚀效果", command=self.erosion_effect).pack(pady=2)
        tk.Button(self.effects_frame, text="膨胀效果", command=self.dilation_effect).pack(pady=2)
        tk.Button(self.effects_frame, text="边缘检测", command=self.edge_detection).pack(pady=2)
        # 中间的图像显示区域
        self.display_frame = tk.Frame(self.root)
        self.display_frame.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)

        # 原图显示区域
        self.original_label = tk.Label(self.display_frame, text="原图")
        self.original_label.pack(side=tk.LEFT, padx=5)
        self.original_canvas = tk.Canvas(self.display_frame, highlightthickness=0)
        self.original_canvas.pack(side=tk.LEFT, padx=5)

        # 处理后图像显示区域
        self.processed_label = tk.Label(self.display_frame, text="处理后")
        self.processed_label.pack(side=tk.LEFT, padx=5)
        self.processed_canvas = tk.Label(self.display_frame)
        self.processed_canvas.pack(side=tk.LEFT, padx=5)

        # 底部按钮
        self.bottom_frame = tk.Frame(self.root)
        self.bottom_frame.pack(side=tk.BOTTOM, pady=5)

        tk.Button(self.bottom_frame, text="应用", command=self.apply_changes).pack(side=tk.LEFT, padx=5)
        tk.Button(self.bottom_frame, text="取消", command=self.cancel_changes).pack(side=tk.LEFT, padx=5)
        tk.Button(self.bottom_frame, text="重置所有", command=self.revert_all).pack(side=tk.LEFT, padx=5)

        # 为原图和处理后的图像添加鼠标事件绑定
        self.original_canvas.bind('<Button-1>', self.start_crop)
        self.original_canvas.bind('<B1-Motion>', self.update_crop)
        self.original_canvas.bind('<ButtonRelease-1>', self.end_crop)

        # 添加裁剪确认和取消按钮（初始隐藏）
        self.crop_frame = tk.Frame(self.bottom_frame)
        self.crop_frame.pack(side=tk.LEFT, padx=5)
        self.confirm_crop_btn = tk.Button(self.crop_frame, text="确认裁剪", command=self.confirm_crop)
        self.cancel_crop_btn = tk.Button(self.crop_frame, text="取消裁剪", command=self.cancel_crop)

    def load_image(self):
        try:
            self.logger.info(f"用户 {self.username} 打开图片")
            file_path = filedialog.askopenfilename()
            if file_path:
                self.image = cv2.imread(file_path)
                self.original_image = self.image.copy()
                # 保存所有必要的图片信息
                self.current_filename = os.path.basename(file_path)
                self.current_filepath = file_path
                self.current_format = os.path.splitext(file_path)[1][1:].lower()
                # 获取文件大小（以字节为单位）
                if os.path.exists(self.current_filepath):
                    file_size = os.path.getsize(self.current_filepath)
                else:
                    file_size = 0
                # 获取当前时间
                current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                
                # 重置当前图片ID
                if hasattr(self, 'current_image_id'):
                    delattr(self, 'current_image_id')
                
                self.show_image()
                # 记录打开新图片的操作
                self.log_process("打开图片", f"文件路径: {file_path}")
        except Exception as e:
            self.logger.error(f"打开图片失败: {str(e)}", exc_info=True)
            raise

    def show_image(self):
        try:
            if self.image is not None:
                # 调整图像大小以适应显示
                height, width = self.image.shape[:2]
                ratio = min(self.display_width / width, self.display_height / height)
                new_size = (int(width * ratio), int(height * ratio))

                # 显示原图
                original_display = cv2.resize(self.original_image, new_size)
                original_display = cv2.cvtColor(original_display, cv2.COLOR_BGR2RGB)
                original_display = Image.fromarray(original_display)
                self.original_photo = ImageTk.PhotoImage(image=original_display)

                # 设置Canvas的大小并显示图片
                self.original_canvas.config(width=new_size[0], height=new_size[1])
                self.original_canvas.create_image(0, 0, image=self.original_photo, anchor='nw')

                # 显示处理后的图片
                processed_display = cv2.resize(self.image, new_size)
                processed_display = cv2.cvtColor(processed_display, cv2.COLOR_BGR2RGB)
                processed_display = Image.fromarray(processed_display)
                self.processed_photo = ImageTk.PhotoImage(image=processed_display)
                self.processed_canvas.config(image=self.processed_photo)
                self.processed_canvas.image = self.processed_photo
        except Exception as e:
            self.logger.error(f"显示图像失败: {str(e)}", exc_info=True)
            raise

    def negative_effect(self):
        if self.image is not None:
            self.image = 255 - self.image
            self.show_image()
            self.apply_changes()
            self.log_process("反相效果")

    def bw_effect(self):
        if self.image is not None:
            self.image = cv2.cvtColor(self.image, cv2.COLOR_BGR2GRAY)
            self.image = cv2.cvtColor(self.image, cv2.COLOR_GRAY2BGR)
            self.show_image()
            self.apply_changes()
            self.log_process("黑白效果")

    def stylization_effect(self):
        if self.image is not None:
            self.image = cv2.stylization(self.image, sigma_s=60, sigma_r=0.6)
            self.show_image()
            self.apply_changes()
            self.log_process("风格化")

    def sketch_effect(self):
        if self.image is not None:
            gray = cv2.cvtColor(self.image, cv2.COLOR_BGR2GRAY)
            inv_gray = 255 - gray
            blur = cv2.GaussianBlur(inv_gray, (21, 21), 0)
            self.image = cv2.divide(gray, 255 - blur, scale=256)
            self.image = cv2.cvtColor(self.image, cv2.COLOR_GRAY2BGR)
            self.show_image()
            self.apply_changes()
            self.log_process("素描效果")

    def save_image(self):
        try:
            self.logger.info(f"用户 {self.username} 保存图片")
            if self.image is not None:
                # 定义支持的文件类型
                filetypes = [
                    ('JPEG 文件', '*.jpg;*.jpeg'),
                    ('PNG 文件', '*.png'),
                    ('BMP 文件', '*.bmp'),
                    ('所有文件', '*.*')
                ]
                # 打开保存文件对话框
                file_path = filedialog.asksaveasfilename(
                    defaultextension=".jpg",
                    filetypes=filetypes,
                    title="保存图片"
                )

                if file_path:
                    try:
                        # 根据文件扩展名保存图片
                        ext = file_path.lower().split('.')[-1]

                        # 转换颜色空间（如果需要）
                        if ext in ['jpg', 'jpeg']:
                            # JPEG格式需要BGR颜色空间
                            save_image = self.image
                        elif ext == 'png':
                            # PNG格式可以保存透明通道
                            save_image = cv2.cvtColor(self.image, cv2.COLOR_BGR2BGRA)
                        else:
                            save_image = self.image

                        # 保存图片
                        cv2.imwrite(file_path, save_image)
                        messagebox.showinfo("成功", "图片保存成功！")
                    except Exception as e:
                        messagebox.showerror("错误", f"保存图片时出错：{str(e)}")
        except Exception as e:
            self.logger.error(f"保存图片失败: {str(e)}", exc_info=True)
            raise

    def apply_changes(self):
        if self.image is not None:
            # 保存当前更改到历史记录
            self.current_step += 1
            # 如果在历史中间进行了新的操作，删除后面的历史
            if self.current_step < len(self.history):
                self.history = self.history[:self.current_step]
            self.history.append(self.image.copy())
            self.log_process("应用更改")

    def cancel_changes(self):
        # 撤销上一步操作
        if self.current_step > 0:
            self.current_step -= 1
            self.image = self.history[self.current_step].copy()
            self.show_image()
        elif self.current_step == 0:
            # 如果是第一步，则恢复到原图
            self.image = self.original_image.copy()
            self.current_step = -1
            self.history = []
            self.show_image()

    def revert_all(self):
        # 重置所有更改，回到原始图片
        if hasattr(self, 'original_image'):
            self.image = self.original_image.copy()
            self.current_step = -1
            self.history = []
            self.show_image()

    def crop_image(self):
        if self.image is not None:
            self.is_cropping = True
            # 显示裁剪确认和取消按钮
            self.confirm_crop_btn.pack(side=tk.LEFT, padx=2)
            self.cancel_crop_btn.pack(side=tk.LEFT, padx=2)
            messagebox.showinfo("提示", "请在原图上拖动鼠标选择要裁剪的区域")

    def start_crop(self, event):
        if self.is_cropping:
            self.crop_start_x = event.x
            self.crop_start_y = event.y

    def update_crop(self, event):
        if self.is_cropping and self.crop_start_x is not None:
            self.crop_end_x = event.x
            self.crop_end_y = event.y
            # 直接在Canvas上绘制选择框
            self.original_canvas.delete("crop_rect")  # 删除旧的选择框
            self.original_canvas.create_rectangle(
                self.crop_start_x, self.crop_start_y,
                self.crop_end_x, self.crop_end_y,
                outline="red", width=2, tags="crop_rect"
            )

    def end_crop(self, event):
        if self.is_cropping:
            self.crop_end_x = event.x
            self.crop_end_y = event.y

    def confirm_crop(self):
        if self.is_cropping and all(x is not None for x in
                                    [self.crop_start_x, self.crop_start_y, self.crop_end_x, self.crop_end_y]):
            # 获取原始图像尺寸和显示尺寸的比例
            height, width = self.image.shape[:2]
            display_height, display_width = self.processed_photo.height(), self.processed_photo.width()
            ratio_x = width / display_width
            ratio_y = height / display_height

            # 计算实际裁剪坐标
            start_x = int(min(self.crop_start_x, self.crop_end_x) * ratio_x)
            start_y = int(min(self.crop_start_y, self.crop_end_y) * ratio_y)
            end_x = int(max(self.crop_start_x, self.crop_end_x) * ratio_x)
            end_y = int(max(self.crop_start_y, self.crop_end_y) * ratio_y)

            # 确保坐标在有效范围内
            start_x = max(0, start_x)
            start_y = max(0, start_y)
            end_x = min(width, end_x)
            end_y = min(height, end_y)

            # 执行裁剪
            self.image = self.image[start_y:end_y, start_x:end_x]
            self.show_image()

            # 清理裁剪状态
            self.cancel_crop()

    def cancel_crop(self):
        self.is_cropping = False
        self.crop_start_x = None
        self.crop_start_y = None
        self.crop_end_x = None
        self.crop_end_y = None

        # 删除选择框
        self.original_canvas.delete("crop_rect")
        self.confirm_crop_btn.pack_forget()
        self.cancel_crop_btn.pack_forget()

    def add_text(self):
        if self.image is not None:
            self.is_adding_text = True
            self.show_text_dialog()
            messagebox.showinfo("提示", "请在图片上点击要添加文字的位置")
            # 绑定鼠标点击事件
            self.processed_canvas.bind('<Button-1>', self.get_text_position)

    def show_text_dialog(self):
        # 创建文字设置对话框
        self.text_dialog = tk.Toplevel(self.root)
        self.text_dialog.title("文字设置")
        self.text_dialog.geometry("300x400")

        # 文字输入
        tk.Label(self.text_dialog, text="输入文字:").pack(pady=5)
        self.text_entry = tk.Entry(self.text_dialog, width=30)
        self.text_entry.pack(pady=5)

        # 字体大小滑块
        tk.Label(self.text_dialog, text="字体大小:").pack(pady=5)
        self.font_size = tk.Scale(self.text_dialog, from_=10, to=100,
                                  orient=tk.HORIZONTAL, length=200)
        self.font_size.set(30)  # 默认大小
        self.font_size.pack(pady=5)
        # 颜色选择
        tk.Label(self.text_dialog, text="文字颜色:").pack(pady=5)
        colors_frame = tk.Frame(self.text_dialog)
        colors_frame.pack(pady=5)

        self.color_var = tk.StringVar(value="white")
        colors = {
            "白色": (255, 255, 255),
            "黑色": (0, 0, 0),
            "红色": (0, 0, 255),
            "绿色": (0, 255, 0),
            "蓝色": (255, 0, 0),
            "黄色": (0, 255, 255)
        }

        # 创建颜色选择按钮
        for i, (color_name, rgb) in enumerate(colors.items()):
            btn = tk.Radiobutton(colors_frame, text=color_name,
                                 variable=self.color_var, value=color_name)
            btn.grid(row=i // 3, column=i % 3, padx=5, pady=2)
            # 字体粗细
            tk.Label(self.text_dialog, text="字体粗细:").pack(pady=5)
            self.thickness = tk.Scale(self.text_dialog, from_=1, to=5,
                                      orient=tk.HORIZONTAL, length=200)
            self.thickness.set(2)  # 默认粗细
            self.thickness.pack(pady=5)

            # 确认和取消按钮
            buttons_frame = tk.Frame(self.text_dialog)
            buttons_frame.pack(pady=10)
            tk.Button(buttons_frame, text="确认",
                      command=self.apply_text).pack(side=tk.LEFT, padx=10)
            tk.Button(buttons_frame, text="取消",
                      command=self.cancel_text).pack(side=tk.LEFT, padx=10)

    def get_text_position(self,event):
        if self.is_adding_text:
            #获取点击位置
            self.text_position = (event.x,event.y)
            #预览效果
            self.preview_text()

    def preview_text(self):
        if self.text_position and self.text_entry.get():
            # 创建图像副本用于预览
            preview_image = self.image.copy()

            # 获取设置
            text = self.text_entry.get()
            font_size = self.font_size.get()
            thickness = self.thickness.get()

            # 获取颜色RGB值
            colors = {
                "白色": (255, 255, 255),
                "黑色": (0, 0, 0),
                "红色": (0, 0, 255),
                "绿色": (0, 255, 0),
                "蓝色": (255, 0, 0),
                "黄色": (0, 255, 255)
            }
            color = colors[self.color_var.get()]

            # 计算实际位置（考虑图像缩放）
            height, width = self.image.shape[:2]
            display_height, display_width = self.processed_photo.height(), self.processed_photo.width()
            ratio_x = width / display_width
            ratio_y = height / display_height

            actual_x = int(self.text_position[0] * ratio_x)
            actual_y = int(self.text_position[1] * ratio_y)

            # 添加文字
            cv2.putText(preview_image, text, (actual_x, actual_y),
                        cv2.FONT_HERSHEY_SIMPLEX, font_size / 30, color, thickness)

            # 更新预览
            self.image = preview_image
            self.show_image()

    def apply_text(self):
        if self.text_position and self.text_entry.get():
            # 文字已经添加到图像上，只需要清理状态
            self.cancel_text()

    def cancel_text(self):
        self.is_adding_text = False
        self.text_position = None
        if hasattr(self, 'text_dialog'):
            self.text_dialog.destroy()
        # 解除鼠标绑定
        self.processed_canvas.unbind('<Button-1>')

    def draw_mode(self):
        if self.image is not None:
            self.is_drawing = True
            self.show_draw_dialog()
            messagebox.showinfo("提示", "请在右侧图片上绘制。按ESC键退出绘图模式")
            # 绑定鼠标事件和键盘事件
            self.processed_canvas.bind('<Button-1>', self.start_draw)
            self.processed_canvas.bind('<B1-Motion>', self.draw)
            self.processed_canvas.bind('<ButtonRelease-1>', self.stop_draw)
            self.root.bind('<Escape>', self.exit_draw_mode)

    def show_draw_dialog(self):
        # 创建绘图设置对话框
        self.draw_dialog = tk.Toplevel(self.root)
        self.draw_dialog.title("绘图设置")
        self.draw_dialog.geometry("200x300")

        # 画笔颜色选择
        tk.Label(self.draw_dialog, text="画笔颜色:").pack(pady=5)
        colors_frame = tk.Frame(self.draw_dialog)
        colors_frame.pack(pady=5)

        self.color_var = tk.StringVar(value="红色")
        colors = {
            "红色": (0, 0, 255),
            "绿色": (0, 255, 0),
            "蓝色": (255, 0, 0),
            "黄色": (0, 255, 255),
            "白色": (255, 255, 255),
            "黑色": (0, 0, 0)
        }

        # 创建颜色选择按钮
        for i, (color_name, rgb) in enumerate(colors.items()):
            btn = tk.Radiobutton(colors_frame, text=color_name,
                                 variable=self.color_var, value=color_name,
                                 command=lambda c=rgb: self.change_draw_color(c))
            btn.grid(row=i // 2, column=i % 2, padx=5, pady=2)

        # 画笔粗细滑块
        tk.Label(self.draw_dialog, text="画笔粗细:").pack(pady=5)
        self.thickness_slider = tk.Scale(self.draw_dialog, from_=1, to=20,
                                         orient=tk.HORIZONTAL, length=150,
                                         command=self.change_draw_thickness)
        self.thickness_slider.set(self.draw_thickness)
        self.thickness_slider.pack(pady=5)

        # 清除按钮
        # tk.Button(self.draw_dialog, text="清除绘图",
        #          command=self.clear_drawing).pack(pady=10)

    def change_draw_color(self, color):
        self.draw_color = color

    def change_draw_thickness(self, val):
        self.draw_thickness = int(val)

    def start_draw(self, event):
        if self.is_drawing:
            self.last_x = event.x
            self.last_y = event.y

    def draw(self, event):
        if self.is_drawing and self.last_x and self.last_y:
            # 获取实际坐标（考虑图像缩放）
            height, width = self.image.shape[:2]
            display_height, display_width = self.processed_photo.height(), self.processed_photo.width()
            ratio_x = width / display_width
            ratio_y = height / display_height

            start_x = int(self.last_x * ratio_x)
            start_y = int(self.last_y * ratio_y)
            end_x = int(event.x * ratio_x)
            end_y = int(event.y * ratio_y)

            # 在图像上绘制线条
            cv2.line(self.image, (start_x, start_y), (end_x, end_y),
                     self.draw_color, self.draw_thickness)

            # 更新显示
            self.show_image()

            # 更新最后的位置
            self.last_x = event.x
            self.last_y = event.y

    def stop_draw(self, event):
        if self.is_drawing:
            self.last_x = None
            self.last_y = None
            self.apply_changes()

    def clear_drawing(self):
        if hasattr(self, 'original_image'):
            self.image = self.history[
                self.current_step].copy() if self.current_step >= 0 else self.original_image.copy()
            self.show_image()

    def exit_draw_mode(self, event=None):
        self.is_drawing = False
        if hasattr(self, 'draw_dialog'):
            self.draw_dialog.destroy()
        self.processed_canvas.unbind('<Button-1>')
        self.processed_canvas.unbind('<B1-Motion>')
        self.processed_canvas.unbind('<ButtonRelease-1>')
        self.root.unbind('<Escape>')

    def apply_filters(self):
        if self.image is not None:
            self.show_filter_dialog()

    def show_filter_dialog(self):
        # 创建滤镜设置对话框
        self.filter_dialog = tk.Toplevel(self.root)
        self.filter_dialog.title("滤镜效果")
        self.filter_dialog.geometry("300x500")

        # 创建滤镜按钮
        filters = [
            ("冷色调", self.cool_tone_filter),
            ("暖色调", self.warm_tone_filter),
            ("高对比度", self.high_contrast_filter),
            ("低对比度", self.low_contrast_filter),
            ("锐化", self.sharpen_filter),
            ("柔化", self.soften_filter),
            ("增亮", self.brighten_filter),
            ("降暗", self.darken_filter),
            ("增加饱和度", self.increase_saturation),
            ("降低饱和度", self.decrease_saturation),
            ("复古褐色", self.vintage_filter),
            ("电影效果", self.cinema_filter),
        ]

        for name, command in filters:
            tk.Button(self.filter_dialog, text=name,
                      command=command, width=20).pack(pady=5)

    def cool_tone_filter(self):
        # 增加蓝色通道，降低红色通道
        b, g, r = cv2.split(self.image)
        b = cv2.add(b, 30)
        r = cv2.subtract(r, 30)
        self.image = cv2.merge([b, g, r])
        self.show_image()
        self.apply_changes()
        self.log_process("冷色调")

    def warm_tone_filter(self):
        # 增加红色通道，降低蓝色通道
        b, g, r = cv2.split(self.image)
        b = cv2.subtract(b, 30)
        r = cv2.add(r, 30)
        self.image = cv2.merge([b, g, r])
        self.show_image()
        self.apply_changes()
        self.log_process("暖色调")

    def high_contrast_filter(self):
        # 增加对比度
        lab = cv2.cvtColor(self.image, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        l = clahe.apply(l)
        lab = cv2.merge([l, a, b])
        self.image = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
        self.show_image()
        self.apply_changes()
        self.log_process("高对比度")

    def low_contrast_filter(self):
        # 降低对比度
        self.image = cv2.convertScaleAbs(self.image, alpha=0.8, beta=30)
        self.show_image()
        self.apply_changes()
        self.log_process("低对比度")

    def sharpen_filter(self):
        # 锐化
        kernel = np.array([[-1, -1, -1],
                           [-1, 9, -1],
                           [-1, -1, -1]])
        self.image = cv2.filter2D(self.image, -1, kernel)
        self.show_image()
        self.apply_changes()
        self.log_process("锐化")

    def soften_filter(self):
        # 柔化
        self.image = cv2.GaussianBlur(self.image, (5, 5), 0)
        self.show_image()
        self.apply_changes()
        self.log_process("柔化")

    def brighten_filter(self):
        # 增加亮度
        self.image = cv2.convertScaleAbs(self.image, alpha=1.2, beta=30)
        self.show_image()
        self.apply_changes()
        self.log_process("增亮")

    def darken_filter(self):
        # 降低亮度
        self.image = cv2.convertScaleAbs(self.image, alpha=0.8, beta=-30)
        self.show_image()
        self.apply_changes()
        self.log_process("降暗")

    def increase_saturation(self):
        # 增加饱和度
        hsv = cv2.cvtColor(self.image, cv2.COLOR_BGR2HSV)
        h, s, v = cv2.split(hsv)
        s = cv2.add(s, 30)
        hsv = cv2.merge([h, s, v])
        self.image = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
        self.show_image()
        self.apply_changes()
        self.log_process("增加饱和度")

    def decrease_saturation(self):
        # 降低饱和度
        hsv = cv2.cvtColor(self.image, cv2.COLOR_BGR2HSV)
        h, s, v = cv2.split(hsv)
        s = cv2.subtract(s, 30)
        hsv = cv2.merge([h, s, v])
        self.image = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
        self.show_image()
        self.apply_changes()
        self.log_process("降低饱和度")

    def vintage_filter(self):
        # 复古效果
        kernel = np.ones((3, 3), np.float32) / 9
        self.image = cv2.filter2D(self.image, -1, kernel)

        # 调整颜色
        b, g, r = cv2.split(self.image)
        r = cv2.add(r, 30)
        b = cv2.subtract(b, 20)
        self.image = cv2.merge([b, g, r])

        # 降低饱和度
        hsv = cv2.cvtColor(self.image, cv2.COLOR_BGR2HSV)
        h, s, v = cv2.split(hsv)
        s = cv2.subtract(s, 40)
        hsv = cv2.merge([h, s, v])
        self.image = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)

        self.show_image()
        self.apply_changes()
        self.log_process("复古效果")

    def cinema_filter(self):
        # 电影效果
        # 增加对比度
        self.image = cv2.convertScaleAbs(self.image, alpha=1.3, beta=0)

        # 调整色调
        b, g, r = cv2.split(self.image)
        r = cv2.add(r, 10)
        b = cv2.add(b, 10)
        self.image = cv2.merge([b, g, r])

        # 添加暗角效果
        rows, cols = self.image.shape[:2]
        kernel_x = cv2.getGaussianKernel(cols, 200)
        kernel_y = cv2.getGaussianKernel(rows, 200)
        kernel = kernel_y * kernel_x.T
        mask = 255 * kernel / np.linalg.norm(kernel)
        for i in range(3):
            self.image[:, :, i] = self.image[:, :, i] * mask

        self.show_image()
        self.apply_changes()
        self.log_process("电影效果")

    def blur_image(self):
        if self.image is not None:
            self.image = cv2.GaussianBlur(self.image, (5, 5), 0)
            self.show_image()
            self.apply_changes()
            self.log_process("模糊处理")

    def adjust_levels(self):
        if self.image is not None:
            self.show_levels_dialog()

    def show_levels_dialog(self):
        # 创建色阶调整对话框
        self.levels_dialog = tk.Toplevel(self.root)
        self.levels_dialog.title("调整色阶")
        self.levels_dialog.geometry("400x500")

        # 亮度调节
        tk.Label(self.levels_dialog, text="亮度:").pack(pady=5)
        self.brightness_scale = tk.Scale(self.levels_dialog, from_=-100, to=100,
                                         orient=tk.HORIZONTAL, length=300,
                                         command=self.update_levels)
        self.brightness_scale.set(0)
        self.brightness_scale.pack(pady=5)

        # 对比度调节
        tk.Label(self.levels_dialog, text="对比度:").pack(pady=5)
        self.contrast_scale = tk.Scale(self.levels_dialog, from_=-100, to=100,
                                       orient=tk.HORIZONTAL, length=300,
                                       command=self.update_levels)
        self.contrast_scale.set(0)
        self.contrast_scale.pack(pady=5)

        # RGB通道调节
        channels_frame = tk.LabelFrame(self.levels_dialog, text="RGB通道调节")
        channels_frame.pack(pady=10, padx=5, fill="x")

        # 红色通道
        tk.Label(channels_frame, text="红色:").pack(pady=5)
        self.red_scale = tk.Scale(channels_frame, from_=-100, to=100,
                                  orient=tk.HORIZONTAL, length=300,
                                  command=self.update_levels)
        self.red_scale.set(0)
        self.red_scale.pack(pady=5)

        # 绿色通道
        tk.Label(channels_frame, text="绿色:").pack(pady=5)
        self.green_scale = tk.Scale(channels_frame, from_=-100, to=100,
                                    orient=tk.HORIZONTAL, length=300,
                                    command=self.update_levels)
        self.green_scale.set(0)
        self.green_scale.pack(pady=5)

        # 蓝色通道
        tk.Label(channels_frame, text="蓝色:").pack(pady=5)
        self.blue_scale = tk.Scale(channels_frame, from_=-100, to=100,
                                   orient=tk.HORIZONTAL, length=300,
                                   command=self.update_levels)
        self.blue_scale.set(0)
        self.blue_scale.pack(pady=5)

        # 按钮区域
        buttons_frame = tk.Frame(self.levels_dialog)
        buttons_frame.pack(pady=10)

        tk.Button(buttons_frame, text="重置",
                  command=self.reset_levels).pack(side=tk.LEFT, padx=10)
        tk.Button(buttons_frame, text="确定",
                  command=self.apply_levels).pack(side=tk.LEFT, padx=10)
        tk.Button(buttons_frame, text="取消",
                  command=self.cancel_levels).pack(side=tk.LEFT, padx=10)

        # 保存原始图像用于预览
        self.levels_original = self.image.copy()

    def update_levels(self, event=None):
        if hasattr(self, 'levels_original'):
            # 获取当前滑块值
            brightness = self.brightness_scale.get()
            contrast = self.contrast_scale.get()
            red = self.red_scale.get()
            green = self.green_scale.get()
            blue = self.blue_scale.get()

            # 复制原始图像进行调整
            self.image = self.levels_original.copy()

            # 调整亮度和对比度
            alpha = (contrast + 100) / 100.0  # 对比度因子
            beta = brightness  # 亮度调整值
            self.image = cv2.convertScaleAbs(self.image, alpha=alpha, beta=beta)

            # 调整RGB通道
            b, g, r = cv2.split(self.image)

            # 调整红色通道
            if red > 0:
                r = cv2.add(r, red)
            else:
                r = cv2.subtract(r, abs(red))

            # 调整绿色通道
            if green > 0:
                g = cv2.add(g, green)
            else:
                g = cv2.subtract(g, abs(green))

            # 调整蓝色通道
            if blue > 0:
                b = cv2.add(b, blue)
            else:
                b = cv2.subtract(b, abs(blue))

            # 合并通道
            self.image = cv2.merge([b, g, r])

            # 更新显示
            self.show_image()

            # 添加日志记录
            self.log_process("色阶调整", f"亮度:{brightness},对比度:{contrast},RGB:({red},{green},{blue})")

    def reset_levels(self):
        # 重置所有滑块到0
        self.brightness_scale.set(0)
        self.contrast_scale.set(0)
        self.red_scale.set(0)
        self.green_scale.set(0)
        self.blue_scale.set(0)

        # 恢复原始图像
        self.image = self.levels_original.copy()
        self.show_image()

    def apply_levels(self):
        # 应用当前调整并关闭对话框
        self.apply_changes()
        self.levels_dialog.destroy()

    def cancel_levels(self):
        # 取消调整，恢复原始图像
        self.image = self.levels_original.copy()
        self.show_image()
        self.levels_dialog.destroy()

    def rotate_image(self):
        if self.image is not None:
            self.image = cv2.rotate(self.image, cv2.ROTATE_90_CLOCKWISE)
            self.show_image()
            self.apply_changes()
            self.log_process("旋转图片")

    def flip_image(self):
        if self.image is not None:
            self.image = cv2.flip(self.image, 1)
            self.show_image()
            self.apply_changes()
            self.log_process("翻转图片")

    def emboss_effect(self):
        if self.image is not None:
            # 创建emboss卷积核
            kernel = np.array([[-2, -1, 0],
                               [-1, 1, 1],
                               [0, 1, 2]])
            # 应用卷积
            self.image = cv2.filter2D(self.image, -1, kernel) + 128
            self.show_image()
            self.apply_changes()
            self.log_process("浮雕效果")

    def sepia_effect(self):
        if self.image is not None:
            # 转换为float32
            img_float = np.float32(self.image)
            # 应用sepia矩阵
            sepia_matrix = np.array([[0.272, 0.534, 0.131],
                                     [0.349, 0.686, 0.168],
                                     [0.393, 0.769, 0.189]])
            self.image = cv2.transform(img_float, sepia_matrix)
            # 确保像素值在0-255范围内
            self.image = np.clip(self.image, 0, 255).astype(np.uint8)
            self.show_image()
            self.apply_changes()
            self.log_process("复古效果")

    def binary_threshold(self):
        if self.image is not None:
            # 转换为灰度图
            gray = cv2.cvtColor(self.image, cv2.COLOR_BGR2GRAY)
            # 应用二值化
            _, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
            # 转回BGR以便显示
            self.image = cv2.cvtColor(binary, cv2.COLOR_GRAY2BGR)
            self.show_image()
            self.apply_changes()
            self.log_process("二值化", "阈值:127")

    def erosion_effect(self):
        if self.image is not None:
            # 创建核
            kernel = np.ones((5, 5), np.uint8)
            # 应用腐蚀
            self.image = cv2.erode(self.image, kernel, iterations=1)
            self.show_image()
            self.apply_changes()

    def dilation_effect(self):
        if self.image is not None:
            # 创建核
            kernel = np.ones((5, 5), np.uint8)
            # 应用膨胀
            self.image = cv2.dilate(self.image, kernel, iterations=1)
            self.show_image()
            self.apply_changes()

    def edge_detection(self):
        """
        对当前加载的图像进行Canny边缘检测
        """
        if self.image is not None:
            # 将图像转换为灰度图，Canny边缘检测需要灰度图像作为输入
            gray = cv2.cvtColor(self.image, cv2.COLOR_BGR2GRAY)
            # 进行Canny边缘检测，这里的阈值可以根据实际情况调整
            edges = cv2.Canny(gray, 50, 150)
            # 更新图像显示
            self.image = edges
            self.show_image()
        else:
            messagebox.showwarning("警告", "请先加载图像")

    def on_closing(self):
        """窗口关闭时的处理"""
        if messagebox.askyesno("退出", "确定要退出程序吗？"):
            # 清除登录状态
            from login_interceptor import LoginInterceptor
            LoginInterceptor.clear_login_status()
            self.root.destroy()

    def log_process(self, process_type, parameters=None):
        """
        记录图像处理操作到process_logs表
        :param process_type: 处理类型
        :param parameters: 处理参数
        """
        try:
            from db_manager import DatabaseManager
            import os
            
            db = DatabaseManager()
            conn = db.get_connection()
            cursor = conn.cursor()
            
            # 首先获取或创建图片记录
            if not hasattr(self, 'current_image_id'):
                # 确保有所有必要的图片信息
                if not hasattr(self, 'current_filename'):
                    self.current_filename = "未命名图片.jpg"
                if not hasattr(self, 'current_filepath'):
                    self.current_filepath = "未知路径"
                if not hasattr(self, 'current_format'):
                    self.current_format = "jpg"
                
                # 获取文件大小（以字节为单位）
                if os.path.exists(self.current_filepath):
                    file_size = os.path.getsize(self.current_filepath)
                else:
                    file_size = 0
                
                # 获取当前时间
                current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                
                # 插入图片记录
                cursor.execute("""
                    INSERT INTO images 
                    (user_id, filename, filepath, format, size, upload_time) 
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (self.user_id, self.current_filename, self.current_filepath, 
                      self.current_format, file_size, current_time))
                self.current_image_id = cursor.lastrowid
            
            # 插入处理记录到process_logs表
            cursor.execute("""
                INSERT INTO process_logs 
                (user_id, image_id, process_type, parameters, process_time) 
                VALUES (?, ?, ?, ?, datetime('now'))
            """, (self.user_id, self.current_image_id, process_type, parameters))
            
            conn.commit()
            conn.close()
            
            # 同时记录到日志文件
            self.logger.info(f"用户 {self.username} 进行{process_type}处理: {parameters if parameters else ''}")
        except Exception as e:
            self.logger.error(f"记录处理操作失败: {str(e)}", exc_info=True)

if __name__ == "__main__":
    from main import start_application
    start_application()

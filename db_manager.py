import sqlite3
from datetime import datetime


class DatabaseManager:
    def __init__(self, db_name='image_process.db'):
        self.db_name = db_name
        self.init_database()

    def get_connection(self):
        """创建并返回数据库连接"""
        return sqlite3.connect(self.db_name)

    def init_database(self):
        """初始化数据库表"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # 创建用户表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                create_time DATETIME NOT NULL,
                last_login DATETIME
            )
        ''')

        # 创建图像表
        cursor.execute('''
           CREATE TABLE IF NOT EXISTS images (
               image_id INTEGER PRIMARY KEY AUTOINCREMENT,
               user_id INTEGER NOT NULL,
               filename TEXT NOT NULL,
               filepath TEXT NOT NULL,
               format TEXT NOT NULL,
               size INTEGER NOT NULL,
               upload_time DATETIME NOT NULL,
               FOREIGN KEY (user_id) REFERENCES users(user_id)
           )
       ''')

        # 创建处理日志表
        cursor.execute('''
           CREATE TABLE IF NOT EXISTS process_logs (
               log_id INTEGER PRIMARY KEY AUTOINCREMENT,
               image_id INTEGER NOT NULL,
               user_id INTEGER NOT NULL,
               process_type TEXT NOT NULL,
               parameters TEXT,
               process_time DATETIME NOT NULL,
               FOREIGN KEY (image_id) REFERENCES images(image_id),
               FOREIGN KEY (user_id) REFERENCES users(user_id)
           )
       ''')

        conn.commit()
        conn.close()

    def add_user(self, username, password, email):
        """添加新用户"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
               INSERT INTO users (username, password, email, create_time)
               VALUES (?, ?, ?, ?)
           ''', (username, password, email, datetime.now()))
            conn.commit()
            return True
        except sqlite3.Error:
            return False
        finally:
            conn.close()

    def check_user(self, username, password):
        """验证用户登录"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                SELECT user_id FROM users 
                WHERE username=? AND password=?
            ''', (username, password))
            return cursor.fetchone()
        finally:
            conn.close()

    def update_last_login(self, username):
        """更新最后登录时间"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                UPDATE users SET last_login=? WHERE username=?
            ''', (datetime.now(), username))
            conn.commit()
        finally:
            conn.close()

    def check_username_exists(self, username):
        """检查用户名是否存在"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT * FROM users WHERE username=?", (username,))
            return cursor.fetchone() is not None
        finally:
            conn.close()

    def check_email_exists(self, email):
        """检查邮箱是否已被注册"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT * FROM users WHERE email=?", (email,))
            return cursor.fetchone() is not None
        finally:
            conn.close()

    def add_image(self, user_id, filename, filepath, format, size):
        """添加图像记录"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                   INSERT INTO images (user_id, filename, filepath, format, size, upload_time)
                   VALUES (?, ?, ?, ?, ?, ?)
               ''', (user_id, filename, filepath, format, size, datetime.now()))
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()

    def add_process_log(self, image_id, user_id, process_type, parameters=None):
        """添加处理日志"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO process_logs (image_id, user_id, process_type, parameters, process_time)
                VALUES (?, ?, ?, ?, ?)
            ''', (image_id, user_id, process_type, parameters, datetime.now()))
            conn.commit()
        finally:
            conn.close()

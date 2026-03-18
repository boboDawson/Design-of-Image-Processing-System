import tkinter as tk
from login_system import LoginSystem
from login_interceptor import LoginInterceptor
import sys
from logger_config import LoggerConfig
import logging

# 在程序开始时初始化日志
logger = LoggerConfig.setup_logger()

def start_application():
    try:
        # 记录程序启动
        logger.info("程序启动")
        
        # 检查登录状态
        login_info = LoginInterceptor.check_login()

        if not login_info:
            logger.info("用户未登录，启动登录界面")
            # 如果未登录，启动登录界面
            login_app = LoginSystem()
            login_app.run()
            # 登录界面关闭后，重新检查登录状态
            login_info = LoginInterceptor.check_login()
            if not login_info:
                logger.warning("用户取消登录，程序退出")
                sys.exit()
        
        # 记录登录成功
        user_id, username = login_info
        logger.info(f"用户 {username}(ID:{user_id}) 登录成功")
        
        # 如果已登录，启动主程序
        from image_editor import ImageEditor
        root = tk.Tk()
        app = ImageEditor(root)
        app.set_user(user_id, username)
        root.mainloop()
        
    except Exception as e:
        logger.error(f"程序发生错误: {str(e)}", exc_info=True)
        raise


if __name__ == "__main__":
    start_application()
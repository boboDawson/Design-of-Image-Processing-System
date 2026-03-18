import logging
import os
from datetime import datetime

class LoggerConfig:
    @staticmethod
    def setup_logger():
        # 创建logs文件夹（如果不存在）
        if not os.path.exists('logs'):
            os.makedirs('logs')
            
        # 设置日志文件名（使用日期）
        log_filename = f'logs/system_{datetime.now().strftime("%Y%m%d")}.log'
        
        # 配置日志
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s [%(levelname)s] %(message)s',
            handlers=[
                logging.FileHandler(log_filename, encoding='utf-8'),
                logging.StreamHandler()  # 同时输出到控制台
            ]
        )
        
        return logging.getLogger() 
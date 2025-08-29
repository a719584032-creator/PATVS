# -*- coding: utf-8 -*-
"""
日志处理
"""
import logging
import sys
from loguru import logger as _logger
import os
from datetime import datetime
from config_manager.config import env_config

# 定义一个变量来标记是否在服务器上运行
IS_SERVER = env_config.global_setting.is_server
# 获取当前日期，格式为 YYYY-MM-DD
current_date = datetime.now().strftime('%Y%m%d')
if IS_SERVER:
    directory = f"/tmp/patvs/{current_date}"
else:
    directory = f"C:\\PATVS\\{current_date}"
if not os.path.exists(directory):
    os.makedirs(directory)
    os.chmod(directory, 0o777)  # 设置目录权限为可读写


# 函数用于检查是否是控制台
def is_console():
    return os.path.basename(sys.executable) == 'python.exe' or \
           os.path.basename(sys.executable) == 'python3.exe' or \
           os.path.basename(sys.executable) == 'pythonw.exe'


class InterceptHandler(logging.Handler):
    def emit(self, record):
        try:
            level = _logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        _logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())


class Log(object):
    __logger = None

    _config = {
        "handlers": [],
    }

    @classmethod
    def get_logger(cls):
        if cls.__logger is None:
            if is_console():
                # 如果在控制台运行，输出到控制台
                cls._config["handlers"].append({
                    "sink": sys.stdout,
                    "format": "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
                              "<level>[{level}]</level> | "
                              "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
                    "level": "INFO"
                })
            else:
                # 如果是在服务器运行，输出到文件
                cls._config["handlers"].append({
                    "sink": f"{directory}/patvs.log",
                    "serialize": False,
                    "level": "INFO",
                    "retention": "10 days",
                    "rotation": "1 day",
                })
            _logger.configure(handlers=cls._config["handlers"])
            logging.basicConfig(handlers=[InterceptHandler()], level=0)
            cls.__logger = _logger

        return cls.__logger


# 自定义调用
logger = Log().get_logger()


def logging_by_multiple_line(level: str, message: str):
    for line in message.rstrip().splitlines():
        logger.log(level, line)


if __name__ == '__main__':
    logger.info('111111111')
    logger.info(directory)

# -*- coding: utf-8 -*-
"""
日志处理
"""
import logging
import sys
from loguru import logger as _logger
import os


directory = "D:\\PATVS\\dist"
if not os.path.exists(directory):
    os.makedirs(directory)

# 函数用于检查是否是控制台
def is_console():
    # 检查 sys.executable 是否指向 python 解释器
    return os.path.basename(sys.executable) == 'python.exe' or \
           os.path.basename(sys.executable) == 'python3.exe' or \
           os.path.basename(sys.executable) == 'pythonw.exe'

class InterceptHandler(logging.Handler):
    def emit(self, record):
        # Get corresponding Loguru level if it exists
        try:
            level = _logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find caller from where originated the logged message
        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        _logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())


class Log(object):
    __logger = None

    # loguru日志配置
    _config = {
        "handlers": [],
    }

    @classmethod
    def get_logger(cls):
        if cls.__logger is None:
            if is_console():
                # 如果在控制台，则添加日志输出到标准输出的handler
                cls._config["handlers"].append({
                    "sink": sys.stdout,
                    "format": "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
                              "<level>[{level}]</level> | "
                              "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
                    "level": "INFO"
                })
            else:
                # 如果不在控制台，在GUI运行时，仅将日志输出到文件
                cls._config["handlers"].append({
                    "sink": "D:/PATVS/dist/patvs.log",  # 确保文件路径是正确的
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

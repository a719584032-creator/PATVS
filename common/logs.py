# -*- coding: utf-8 -*-
"""
日志处理
"""
import logging
import sys
from loguru import logger as _logger


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
        "handlers": [
            {
                "sink": sys.stdout,
                "format": "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
                      #    "<level>{extra[module]} {extra[case_id]} [{level}] {extra[ctx_id]}</level> | "
                          "<level>[{level}]</level> | "
                          "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
                "level": "INFO"
            },

            # # 日志记录到文件
            {
                "sink": "../file.log",
                "serialize": False,
                "level": "INFO",
               "retention": "10 days",
               "rotation": "1 day",
            },
        ],
   #     "extra": {"module": "\b", "case_id": "\b", "ctx_id": "\b"}
    }

    @classmethod
    def get_logger(cls):
        if cls.__logger is None:
            _logger.configure(**cls._config)
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

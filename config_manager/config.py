# -*- coding: utf-8 -*-
import os
from attr import attrs, attrib
from dotenv import load_dotenv
from common.logs import logger
from common.meta_class import MetaSingleton
from common.tools import Public


@attrs
class _GlobalSetting(object):
    # 主url
    protocol = attrib(default='', type=str)
    domain = attrib(default='', type=str)
    db_host = attrib(default='', type=str)
    db_user = attrib(default='', type=str)
    db_password = attrib(default='', type=str)
    db_database = attrib(default='', type=str)
    db_buffered = attrib(default=True, type=bool)
    aws_user_id = attrib(default='', type=str)
    aws_access_key = attrib(default='', type=str)
    aws_secret_key = attrib(default='', type=str)
    aws_endpoint_url = attrib(default='', type=str)
    aws_region_name = attrib(default='', type=str)
    aws_signature_version = attrib(default='', type=str)
    aws_bucket_name = attrib(default='', type=str)

    def init_from_env(self):
        self.protocol = os.getenv("GLOBAL_SETTING_PROTOCOL")
        self.domain = os.getenv("GLOBAL_SETTING_HOST")
        self.db_host = os.getenv("DB_HOST")
        self.db_user = os.getenv("DB_USER")
        self.db_password = os.getenv("DB_PASSWORD")
        self.db_database = os.getenv("DB_DATABASE")
        self.db_buffered = bool(os.getenv("DB_BUFFERED"))
        self.aws_user_id = os.getenv("AWS_USER_ID")
        self.aws_access_key = os.getenv("AWS_ACCESS_KEY")
        self.aws_secret_key = os.getenv("AWS_SECRET_KEY")
        self.aws_endpoint_url = os.getenv("AWS_ENDPOINT_URL")
        self.aws_region_name = os.getenv("AWS_REGION_NAME")
        self.aws_signature_version = os.getenv("AWS_SIGNATURE_VERSION")
        self.aws_bucket_name = os.getenv("AWS_BUCKET_NAME")


class EnvConfig(metaclass=MetaSingleton):
    def __init__(self):
        self.global_setting = _GlobalSetting()
        self._init_from_env()

    def _init_from_env(self):
        self.global_setting.init_from_env()


# 加载默认配置，不覆盖系统的环境变量
default_cfg_path = f'{Public.get_root_path()}/conf/env.default'
if os.path.exists(default_cfg_path):
    load_dotenv(dotenv_path=default_cfg_path, override=False)

# 加载测试配置，覆盖系统的环境变量
cfg_path = f'{Public.get_root_path()}/conf/.env'
if os.path.exists(cfg_path):
    load_dotenv(dotenv_path=cfg_path, override=True)
env_config = EnvConfig()

if __name__ == "__main__":
    cfg = EnvConfig()
    logger.info(f"test env config: {default_cfg_path}")
    logger.info(f"protocol: {cfg.global_setting.protocol}")
    logger.info(f"password: {cfg.global_setting.aws_user_id}")
    logger.info(f"domain: {cfg.global_setting.domain}")
    logger.info(f"domain: {cfg.global_setting.db_buffered}")
    logger.info(type(cfg.global_setting.db_buffered))

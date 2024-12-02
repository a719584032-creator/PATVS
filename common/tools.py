# -*- coding: utf-8 -*-
import datetime
import random
import re
import string
import time
import os
import sys


class Public(object):

    @staticmethod
    def random_str(num=6) -> str:
        """默认随机6位字母+数字组合"""
        return ''.join([random.choice(string.digits + string.ascii_letters) for i in range(num)])

    @staticmethod
    def random_letter(num=6) -> str:
        """默认随机6位字母"""
        return ''.join([random.choice(string.ascii_letters) for i in range(num)])

    @staticmethod
    def random_special_str(num=6) -> str:
        """默认随机24位包含大写字母、小写字母、数字、带/-.的字符串"""
        char = ["/", "-", "."]

        def inner_str():
            return ''.join([random.choice(string.digits + string.ascii_letters) for i in range(num)])

        return ''.join([inner_str() + i for i in char]) + inner_str()

    @staticmethod
    def timer(func, filter_param, expect_result, second=3, time_out=2) -> str:
        """
        轮询
        :param func: 被测试的函数
        :param filter_param: response 过滤条件
        :param expect_result: 预期结果
        :param second: 秒
        :param time_out: 分钟
        :return:
        """
        start_time = time.time()
        while True:
            result = func().jmespath(filter_param)
            end_time = time.time()
            if int(end_time - start_time) >= time_out * 60:
                raise Exception(
                    f"当前轮询结果: {result} != {expect_result}, timeout {time_out}min \nrequest_url: {func().url} \nresponse: {func().text}")
            elif not result and result != 0:
                time.sleep(second)
                continue
            elif type(result) is list:
                result = func().jmespath(filter_param)[0]
            if result == expect_result:
                break
            time.sleep(second)
        return result

    @staticmethod
    def cur_time(delta=0, strf_time="%Y-%m-%d %H:%M:%S"):
        """
        :param delta: 相对时间，0 当前时间, +1 当前时间 +1 天，-1 当前时间 -1 天
        :param strf_time: 时间格式
        :return:
        """
        if delta == 0:
            return datetime.datetime.now().strftime(strf_time)
        return (datetime.datetime.now() + datetime.timedelta(days=delta)).strftime(strf_time)

    @staticmethod
    def modify_string(string):
        ''' 转小写/使用下划线替换空格 '''
        modified_string = string.lower().replace(' ', '_')
        print(modified_string)
        return modified_string

    @staticmethod
    def get_root_path():
        if getattr(sys, 'frozen', False):  # 判断是否为打包后的环境
            # 打包环境下，返回 PyInstaller 的临时目录
            application_path = sys._MEIPASS
        else:
            # 开发环境下，返回项目的根目录
            application_path = os.path.dirname(os.path.abspath(__file__))  # 当前脚本目录
            # 如果脚本在子目录下（如 common），返回上一级目录
            application_path = os.path.abspath(os.path.join(application_path, '..'))

        return application_path

    @staticmethod
    def resource_path(relative_path):
        """ Get absolute path to resource, works for dev and for PyInstaller """
        base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        return os.path.join(base_path, relative_path)

    @staticmethod
    def get_num(num_string):
        """
        去除单位，仅保留数字
        :return:
        """
        num = re.sub(r'[a-zA-Z%]+', '', num_string)
        return num


if __name__ == '__main__':
    print(Public.modify_string('Does the product contain'))
    print(Public.get_root_path())
    string = '66%'
    print(Public.get_num(string))

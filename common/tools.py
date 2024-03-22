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
        # 如果程序被打包成了单一文件，_MEIPASS 会提供临时目录
        if getattr(sys, 'frozen', False):
            application_path = sys._MEIPASS
        else:
            # 如果程序没有被打包，则使用__file__获取当前文件路径
            application_path = os.path.dirname(__file__)

        # 从应用程序路径构建到数据库的路径
        db_path = os.path.join(application_path, '..', 'sqlite-tools', 'lenovoDb')
        # 规范化路径，消除..等相对元素，获取绝对路径
        root_path = os.path.abspath(db_path)
        return root_path

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

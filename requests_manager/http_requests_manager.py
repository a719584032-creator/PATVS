# -*- coding: utf-8 -*-
# 客户端请求调用
import requests
import os
import json
from common.logs import logger
from config_manager.config import env_config


class HttpRequestManager:
    def __init__(self, base_url):
        self.base_url = base_url

    def get_params(self, endpoint, params=None, token=None):
        try:
            headers = {'x-access-tokens': token}
            response = requests.get(f'{self.base_url}{endpoint}', params=params, headers=headers, verify=False)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f'HTTP GET request to {endpoint} failed: {e}')
            raise

    def post_data(self, endpoint, data=None, token=None):
        try:
            headers = {'x-access-tokens': token}
            response = requests.post(url=f'{self.base_url}{endpoint}', json=data, headers=headers, verify=False)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f'HTTP POST request to {endpoint} failed: {e}')
            raise

    def post_file(self, endpoint, data=None, files=None, token=None):
        try:
            headers = {'x-access-tokens': token}
            response = requests.post(url=f'{self.base_url}{endpoint}', data=data, files=files, headers=headers,
                                     verify=False)
            response.raise_for_status()
            return response
        except requests.RequestException as e:
            logger.error(f'HTTP POST request to {endpoint} failed: {e}')
            raise

    def get_plan_names(self, username, token=None):
        try:
            headers = {'x-access-tokens': token}
            response = requests.get(f'{self.base_url}/get_plan_names/{username}', headers=headers, verify=False)
            response.raise_for_status()
            data = response.json()
            return data.get('plan_names')
        except requests.RequestException as e:
            logger.error(f'HTTP GET request to get_plan_names failed: {e}')
            raise

    def get_sheet_names(self, plan_name, username, token=None):
        try:
            headers = {'x-access-tokens': token}
            params = {'plan_name': plan_name, 'username': username}
            response = requests.get(f'{self.base_url}/get_sheet_names', params=params, headers=headers, verify=False)
            response.raise_for_status()
            data = response.json()
            return data.get('sheet_names_with_ids')
        except requests.RequestException as e:
            logger.error(f'HTTP GET request to /get_plan_names failed: {e}')
            raise

    def update_end_time_case_id(self, case_id, case_result, input_content=None, token=None):
        data = {'case_id': case_id, 'case_result': case_result, 'comment': input_content}
        try:
            headers = {'x-access-tokens': token}
            response = requests.post(f'{self.base_url}/update_end_time', json=data, headers=headers, verify=False)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f'HTTP POST request to /update_end_time failed: {e}')
            raise

    def get_start_time(self, case_id, token=None):
        try:
            headers = {'x-access-tokens': token}
            response = requests.get(f'{self.base_url}/get_start_time/{case_id}', headers=headers, verify=False)
            response.raise_for_status()
            data = response.json()
            logger.warning(data)
            return data.get('start_time')
        except requests.RequestException as e:
            logger.error(f'HTTP GET request to /get_plan_names failed: {e}')
            raise

    def get_cases_by_sheet_id(self, sheet_id, token=None):
        try:
            headers = {'x-access-tokens': token}
            response = requests.get(f'{self.base_url}/get_cases/{sheet_id}', headers=headers, verify=False)
            response.raise_for_status()
            data = response.json()
            return data
        except requests.RequestException as e:
            logger.error(f'HTTP GET request to /get_cases failed: {e}')
            raise


def load_config(env):
    with open('config.json', 'r') as file:
        config = json.load(file)
        return config.get(env, {})



# # 配置管理类实例
base_url = env_config.global_setting.protocol + '://' + env_config.global_setting.domain
http_manager = HttpRequestManager(base_url)

import re
import requests

# 输入字符串
input_string = "[`+2]N5 (02)Under Dos/Shell/PE"

# 使用正则表达式提取方括号内的内容
bracket_contents = re.findall(r'\[([^\]]+)\]', input_string)

print(bracket_contents)

# 提取关键参数
key_params = []
for content in bracket_contents:
    matches = re.match(r'(.+?)\+(\d+)', content)
    if matches:
        key_params.append((matches.group(1), matches.group(2)))

# 打印结果
print(key_params)
data = {'2215': ['dsfd', 'dfsfds', '2215'], '23': ['dsf'], '55': ['fdgfg']}
if '22' in data:
    print(1)
for key, value in data.items():
    print(key)
    print(value)
# print(list(data.keys()))
import pyautogui
import time


def keep_awake():
    try:
        while True:
            pyautogui.press('shift')
            print("按下Shift键")
            time.sleep(10)

            pyautogui.press('ctrl')
            print("按下Ctrl键")
            time.sleep(10)
    except KeyboardInterrupt:
        print("程序已停止")


def add_user(username, role, url):
    data = {'username': username, 'password': '123456', 'role': role}
    r = requests.post(url=url, json=data, verify=False)
    print(r.status_code)


if __name__ == "__main__":
    keep_awake()
    url = 'https://patvs.lenovo.com/add_user'
    #url= 'http://10.184.37.105/add_user'
    #add_user('liangxd5', '', url)
    # list1 = [['时间', '1']]
    # print(len(list1))
    # print('时间' in list1[0])

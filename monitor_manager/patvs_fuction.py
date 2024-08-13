# -*- coding: utf-8 -*-
# 负责监控逻辑
import random

import wx
from common.logs import logger
from monitor_manager.devicerm import Notification
from monitor_manager.lock_screen import monitor_locks
from pynput import mouse
import time
import psutil
import win32evtlog
import pywintypes
import win32evtlogutil
import win32con
import pytz
import datetime
from pynput import keyboard
from cryptography.fernet import Fernet
import base64
import os
import json
import threading
import win32api


class Patvs_Fuction():
    TEMP_FILE = r"D:\PATVS\temp_action_and_num.json"
    ENCRYPTION_KEY = b'JZfpG9N5K4PQoQMtImxPv80DS-D-WPXr9DN0eF7zhR4='  # 32 bytes URL-safe base64-encoded key
    # 定义按键映射字典，将用户友好的名称映射到 pynput 的按键
    KEY_MAPPING = {
        'alt': keyboard.Key.alt,
        'alt_l': keyboard.Key.alt_l,
        'alt_r': keyboard.Key.alt_r,
        'alt_gr': keyboard.Key.alt_gr,
        'backspace': keyboard.Key.backspace,
        'caps_lock': keyboard.Key.caps_lock,
        'cmd': keyboard.Key.cmd,
        'cmd_l': keyboard.Key.cmd_l,
        'cmd_r': keyboard.Key.cmd_r,
        'ctrl': keyboard.Key.ctrl,
        'ctrl_l': keyboard.Key.ctrl_l,
        'ctrl_r': keyboard.Key.ctrl_r,
        'delete': keyboard.Key.delete,
        'down': keyboard.Key.down,
        'end': keyboard.Key.end,
        'enter': keyboard.Key.enter,
        'esc': keyboard.Key.esc,
        'f1': keyboard.Key.f1,
        'f2': keyboard.Key.f2,
        'f3': keyboard.Key.f3,
        'f4': keyboard.Key.f4,
        'f5': keyboard.Key.f5,
        'f6': keyboard.Key.f6,
        'f7': keyboard.Key.f7,
        'f8': keyboard.Key.f8,
        'f9': keyboard.Key.f9,
        'f10': keyboard.Key.f10,
        'f11': keyboard.Key.f11,
        'f12': keyboard.Key.f12,
        'f13': keyboard.Key.f13,
        'f14': keyboard.Key.f14,
        'f15': keyboard.Key.f15,
        'home': keyboard.Key.home,
        'left': keyboard.Key.left,
        'page_down': keyboard.Key.page_down,
        'page_up': keyboard.Key.page_up,
        'right': keyboard.Key.right,
        'shift': keyboard.Key.shift,
        'shift_l': keyboard.Key.shift_l,
        'shift_r': keyboard.Key.shift_r,
        'space': keyboard.Key.space,
        'tab': keyboard.Key.tab,
        'up': keyboard.Key.up,
        'media_play_pause': keyboard.Key.media_play_pause,
        'media_volume_mute': keyboard.Key.media_volume_mute,
        'media_volume_down': keyboard.Key.media_volume_down,
        'media_volume_up': keyboard.Key.media_volume_up,
        'media_previous': keyboard.Key.media_previous,
        'media_next': keyboard.Key.media_next,
        'insert': keyboard.Key.insert,
        'menu': keyboard.Key.menu,
        'num_lock': keyboard.Key.num_lock,
        'pause': keyboard.Key.pause,
        'prtsc': keyboard.Key.print_screen,
        'scrlk': keyboard.Key.scroll_lock,
        'a': keyboard.KeyCode.from_char('a'),
        'b': keyboard.KeyCode.from_char('b'),
        'c': keyboard.KeyCode.from_char('c'),
        'd': keyboard.KeyCode.from_char('d'),
        'e': keyboard.KeyCode.from_char('e'),
        'f': keyboard.KeyCode.from_char('f'),
        'g': keyboard.KeyCode.from_char('g'),
        'h': keyboard.KeyCode.from_char('h'),
        'i': keyboard.KeyCode.from_char('i'),
        'j': keyboard.KeyCode.from_char('j'),
        'k': keyboard.KeyCode.from_char('k'),
        'l': keyboard.KeyCode.from_char('l'),
        'm': keyboard.KeyCode.from_char('m'),
        'n': keyboard.KeyCode.from_char('n'),
        'o': keyboard.KeyCode.from_char('o'),
        'p': keyboard.KeyCode.from_char('p'),
        'q': keyboard.KeyCode.from_char('q'),
        'r': keyboard.KeyCode.from_char('r'),
        's': keyboard.KeyCode.from_char('s'),
        't': keyboard.KeyCode.from_char('t'),
        'u': keyboard.KeyCode.from_char('u'),
        'v': keyboard.KeyCode.from_char('v'),
        'w': keyboard.KeyCode.from_char('w'),
        'x': keyboard.KeyCode.from_char('x'),
        'y': keyboard.KeyCode.from_char('y'),
        'z': keyboard.KeyCode.from_char('z'),
        '`': keyboard.KeyCode.from_char('`'),
        '1': keyboard.KeyCode.from_char('1'),
        '2': keyboard.KeyCode.from_char('2'),
        '3': keyboard.KeyCode.from_char('3'),
        '4': keyboard.KeyCode.from_char('4'),
        '5': keyboard.KeyCode.from_char('5'),
        '6': keyboard.KeyCode.from_char('6'),
        '7': keyboard.KeyCode.from_char('7'),
        '8': keyboard.KeyCode.from_char('8'),
        '9': keyboard.KeyCode.from_char('9'),
        '0': keyboard.KeyCode.from_char('0'),
        '-': keyboard.KeyCode.from_char('-'),
        '=': keyboard.KeyCode.from_char('='),
        '[': keyboard.KeyCode.from_char('['),
        ']': keyboard.KeyCode.from_char(']'),
        '\\': keyboard.KeyCode.from_char('\\'),  # 单反斜杠
        ';': keyboard.KeyCode.from_char(';'),
        ',': keyboard.KeyCode.from_char(','),
        '.': keyboard.KeyCode.from_char('.'),
        '/': keyboard.KeyCode.from_char('/')
    }

    def __init__(self, window, stop_event):
        self.window = window
        self.stop_event = stop_event
        # 读取临时文件
        self.remaining_actions = []
        self.case_id = None
        self.action_complete = threading.Event()
        self.msg_loop_thread_id = None

    def monitor_time(self, num_time):
        """
        监控时间
        """
        count = 0
        num_time = num_time * 60
        wx.CallAfter(self.window.add_log_message, f"等待时间: {num_time} 秒")
        try:
            while self.stop_event and count < num_time:
                count += 1
                time.sleep(1)
                wx.CallAfter(self.window.add_log_message, f"Running time {count} of ")
        finally:
            self.action_complete.set()  # 设置动作完成状态

    def monitor_power_plug_changes(self, target_cycles):
        """
        监控电源插拔次数
        """
        # battery.percent  # 电量百分比
        # battery.power_plugged  # 是否连接电源
        # battery.secsleft  # 剩余时间（秒），未充电时可用
        plugged_in_last_state = None
        plug_unplug_cycles = 0
        try:
            while self.stop_event and plug_unplug_cycles < target_cycles:
                battery = psutil.sensors_battery()
                if battery:
                    plugged_in = battery.power_plugged
                    # 初次运行时设定初始电源状态
                    if plugged_in_last_state is None:
                        plugged_in_last_state = plugged_in

                    # 当电源状态改变时
                    if plugged_in != plugged_in_last_state:
                        plugged_in_last_state = plugged_in

                        # 当检测到拔出动作后计算一次周期
                        if not plugged_in:
                            plug_unplug_cycles += 1
                            message = f"Power plug/unplug cycle completed: {plug_unplug_cycles} times"
                            wx.CallAfter(self.window.add_log_message, message)
                        if plug_unplug_cycles >= target_cycles:
                            wx.CallAfter(self.window.add_log_message,
                                         f"Target power plug/unplug cycles {plug_unplug_cycles} reached. Exiting.")
                            break
                else:
                    logger.error("No battery information found")
                    break
                time.sleep(1)
        finally:
            wx.CallAfter(self.window.add_log_message, "Stopped monitoring power plug/unplug")
            self.action_complete.set()  # 设置动作完成状态

    def count_s3_sleep_events(self, start_time):
        hand = win32evtlog.OpenEventLog(None, "System")
        flags = win32evtlog.EVENTLOG_BACKWARDS_READ | win32evtlog.EVENTLOG_SEQUENTIAL_READ
        total = 0
        start_time = datetime.datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")

        try:
            while True:
                events = win32evtlog.ReadEventLog(hand, flags, 0)
                if not events:
                    break  # If no more events, break the loop
                for event in events:
                    if event.EventID == 507 or event.EventID == 107:
                        occurred_time_str = str(event.TimeGenerated)
                        try:
                            occurred_time = datetime.datetime.strptime(occurred_time_str, "%Y/%m/%d %H:%M:%S")
                        except ValueError:
                            occurred_time = datetime.datetime.strptime(occurred_time_str, "%Y-%m-%d %H:%M:%S")
                        if occurred_time > start_time:
                            total += 1
        finally:
            win32evtlog.CloseEventLog(hand)
            return total

    def test_count_s3_sleep_events(self, start_time, target_cycles):
        hand = win32evtlog.OpenEventLog(None, "System")
        flags = win32evtlog.EVENTLOG_FORWARDS_READ | win32evtlog.EVENTLOG_SEQUENTIAL_READ
        total = 0
        log_num = 0
        start_time = datetime.datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
        try:
            while self.stop_event:
                events = win32evtlog.ReadEventLog(hand, flags, 0)
                if not events:
                    # 重新打开句柄获取监控开始后产生的新S4日志
                    hand = win32evtlog.OpenEventLog(None, "System")
                    log_num = total
                    total = 0
                    time.sleep(3)
                for event in events:
                    if event.EventID == 507 or event.EventID == 107:
                        occurred_time_str = str(event.TimeGenerated)
                        try:
                            occurred_time = datetime.datetime.strptime(occurred_time_str, "%Y/%m/%d %H:%M:%S")
                        except ValueError:
                            occurred_time = datetime.datetime.strptime(occurred_time_str, "%Y-%m-%d %H:%M:%S")
                        if occurred_time > start_time:
                            total += 1
                            # 仅输出增量日志
                            if total > log_num:
                                wx.CallAfter(self.window.add_log_message,
                                             f"当前已测试 {total} 次，目标次数为 {target_cycles} 次。")
                            if total >= target_cycles:
                                wx.CallAfter(self.window.add_log_message,
                                             f"Reached target cycles. S3 sleep events: {total}")
                                return
        finally:
            wx.CallAfter(self.window.add_log_message, "Stopped monitoring S3 sleep events.")
            win32evtlog.CloseEventLog(hand)
            self.action_complete.set()  # 设置动作完成状态

    def get_event_data(self, event):
        # 获取详细信息中的 EventData
        strings = win32evtlogutil.SafeFormatMessage(event, 'System')
        return strings

    def parse_time(self, time_str):
        time_str = time_str.strip()  # 移除空格
        try:
            # 去除小数秒部分，只保留到秒级别
            if '.' in time_str:
                time_str = time_str.split('.')[0]
            utc_time = datetime.datetime.strptime(time_str, "%Y-%m-%dT%H:%M:%S")
            # 设置为UTC时区
            utc_time = utc_time.replace(tzinfo=pytz.utc)
            # 转换为东8区时间
            beijing_time = utc_time.astimezone(pytz.timezone('Asia/Shanghai'))
            # 格式化为所需字符串格式，不包含时区信息
            formatted_time = datetime.datetime.strptime(beijing_time.strftime("%Y-%m-%d %H:%M:%S"), "%Y-%m-%d %H:%M:%S")
            return formatted_time
        except ValueError as e:
            # 解析失败，返回None
            logger.error(f'{e}')
            return None

    def test_count_s4_sleep_events(self, start_time, target_cycles):
        hand = win32evtlog.OpenEventLog(None, "System")
        flags = win32evtlog.EVENTLOG_FORWARDS_READ | win32evtlog.EVENTLOG_SEQUENTIAL_READ
        total = 0
        log_num = 0
        start_time = datetime.datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
        try:
            while self.stop_event:
                events = win32evtlog.ReadEventLog(hand, flags, 0)
                if not events:
                    # 重新打开句柄获取增量日志
                    hand = win32evtlog.OpenEventLog(None, "System")
                    log_num = total
                    total = 0
                    time.sleep(3)
                for event in events:
                    if event.EventID == 1:
                        # 解析 EventData 获取 SleepTime 和 WakeTime
                        event_data = self.get_event_data(event)
                        sleep_time = None
                        wake_time = None
                        for line in event_data.split('\n'):
                            if "睡眠时间" in line:
                                sleep_time = self.parse_time(line.split(": ")[1])
                            elif "唤醒时间" in line:
                                wake_time = self.parse_time(line.split(": ")[1])
                        # 统计S4事件次数
                        if sleep_time and wake_time:
                            if sleep_time > start_time and wake_time > sleep_time:
                                total += 1
                                if total > log_num:  # 仅输出增量日志
                                    wx.CallAfter(self.window.add_log_message,
                                                 f"当前已测试 {total} 次，目标次数为 {target_cycles} 次。")
                                    wx.CallAfter(self.window.add_log_message,
                                                 f'SleepTime: {sleep_time}, WakeTime: {wake_time}')
                                if total >= target_cycles:
                                    wx.CallAfter(self.window.add_log_message,
                                                 f"Reached target cycles. S4 sleep events: {total}")
                                    return
        finally:
            wx.CallAfter(self.window.add_log_message, "Stopped monitoring S4 sleep events.")
            win32evtlog.CloseEventLog(hand)
            self.action_complete.set()  # 设置动作完成状态

    def start_monitoring_s3_and_power(self, target_cycles):
        # 设定开始时间为当前时间
        start_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        logger.info(f"Monitoring started at {start_time}")

        plug_unplug_cycles = 0
        s3_sleep_events = 0

        while plug_unplug_cycles < target_cycles or s3_sleep_events < target_cycles:
            if plug_unplug_cycles < target_cycles:
                plug_unplug_cycles = self.monitor_power_plug_changes(target_cycles - plug_unplug_cycles)

            if s3_sleep_events < target_cycles:
                s3_sleep_events = self.count_s3_sleep_events(start_time=start_time)

            # 两个都达到目标次数后退出循环
            if plug_unplug_cycles >= target_cycles and s3_sleep_events >= target_cycles:
                break
            elif not self.stop_event:
                break
            time.sleep(1)
        message = (
            f"Reached target cycles. Plug/unplug cycles: {plug_unplug_cycles}, S3 sleep events: {s3_sleep_events}")
        wx.CallAfter(self.window.add_log_message, message)
        wx.CallAfter(self.window.after_test)

    def test_count_s5_sleep_events(self, start_time, target_cycles):
        hand = win32evtlog.OpenEventLog(None, "System")
        flags = win32evtlog.EVENTLOG_BACKWARDS_READ | win32evtlog.EVENTLOG_SEQUENTIAL_READ
        total = 0
        log_num = 0
        start_time = datetime.datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
        try:
            while self.stop_event:
                events = win32evtlog.ReadEventLog(hand, flags, 0)
                if not events:
                    # 重新打开句柄获取监控开始后产生的新S4日志
                    hand = win32evtlog.OpenEventLog(None, "System")
                    log_num = total
                    total = 0
                    time.sleep(3)
                for event in events:
                    if event.EventID == 7001:
                        occurred_time_str = str(event.TimeGenerated)
                        try:
                            occurred_time = datetime.datetime.strptime(occurred_time_str, "%Y/%m/%d %H:%M:%S")
                        except ValueError:
                            occurred_time = datetime.datetime.strptime(occurred_time_str, "%Y-%m-%d %H:%M:%S")
                        if occurred_time > start_time:
                            total += 1
                            # 仅输出增量日志
                            if total > log_num:
                                wx.CallAfter(self.window.add_log_message,
                                             f"Reached target cycles. S5 sleep events: {total}")
                            if total >= target_cycles:
                                return
        finally:
            wx.CallAfter(self.window.add_log_message, "Stopped monitoring S5 sleep events.")
            win32evtlog.CloseEventLog(hand)
            self.action_complete.set()  # 设置动作完成状态

    def test_count_restart_events(self, start_time, target_cycles):
        hand = win32evtlog.OpenEventLog(None, "System")
        flags = win32evtlog.EVENTLOG_BACKWARDS_READ | win32evtlog.EVENTLOG_SEQUENTIAL_READ
        total = 0
        log_num = 0
        start_time = datetime.datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
        try:
            while self.stop_event:
                events = win32evtlog.ReadEventLog(hand, flags, 0)
                if not events:
                    # 重新打开句柄获取监控开始后产生的新S4日志
                    hand = win32evtlog.OpenEventLog(None, "System")
                    log_num = total
                    total = 0
                    time.sleep(3)
                for event in events:
                    event_id = event.EventID & 0xFFFF  # 掩码EventID以获取实际值
                    if event_id == 1074:
                        occurred_time_str = str(event.TimeGenerated)
                        try:
                            occurred_time = datetime.datetime.strptime(occurred_time_str, "%Y/%m/%d %H:%M:%S")
                        except ValueError:
                            occurred_time = datetime.datetime.strptime(occurred_time_str, "%Y-%m-%d %H:%M:%S")
                        if occurred_time > start_time:
                            total += 1
                            if total > log_num:
                                wx.CallAfter(self.window.add_log_message,
                                             f"Reached target cycles. ReStart sleep events: {total}")
                            if total >= target_cycles:
                                return
        finally:
            wx.CallAfter(self.window.add_log_message, "Stopped monitoring ReStart sleep events.")
            win32evtlog.CloseEventLog(hand)
            self.action_complete.set()  # 设置动作完成状态

    def monitor_device_plug_changes(self, target_cycles):
        notification = Notification(0, target_cycles, self.window)
        notification.messageLoop()
        self.action_complete.set()  # 设置动作完成状态

    def monitor_lock_screen_changes(self, target_cycles):
        monitor_locks(target_cycles, self.window)
        self.action_complete.set()  # 设置动作完成状态

    def monitor_keystrokes(self, target_cycles, key_name=None):
        try:
            key_count = 0
            key = self.KEY_MAPPING.get(key_name.lower()) if key_name else None

            def on_press(pressed_key):
                nonlocal key_count
                if key is None or pressed_key == key:
                    key_count += 1
                    wx.CallAfter(self.window.add_log_message, f"Key pressed: {key}. Total count: {key_count}")
                if key_count >= target_cycles or not self.stop_event:
                    wx.CallAfter(self.window.add_log_message, "Reached target keystroke count. Exiting...")
                    return False  # Stop the listener
            # Collect events until the target keystroke count is reached
            with keyboard.Listener(on_press=on_press) as listener:
                listener.join()
        finally:
            wx.CallAfter(self.window.add_log_message, "Stopped monitoring keystrokes.")
            self.action_complete.set()  # 设置动作完成状态

    def monitor_mouse_clicks(self, target_cycles):
        try:
            click_count = 0

            def on_click(x, y, button, pressed):
                nonlocal click_count
                if pressed:
                    click_count += 1
                    message = f"Mouse clicked at ({x}, {y}) with {button}. Total count: {click_count}"
                    wx.CallAfter(self.window.add_log_message, message)
                    if click_count >= target_cycles or not self.stop_event:
                        message = "Reached target click count. Exiting..."
                        wx.CallAfter(self.window.add_log_message, message)
                        return False  # Stop the listener

            # Collect events until the target click count is reached
            with mouse.Listener(on_click=on_click) as listener:
                listener.join()
        finally:
            wx.CallAfter(self.window.add_log_message, "Stopped monitoring click.")
            self.action_complete.set()  # 设置动作完成状态

    def encrypt_data(self, data):
        fernet = Fernet(self.ENCRYPTION_KEY)
        encrypted_data = fernet.encrypt(data.encode())
        return encrypted_data

    def decrypt_data(self, encrypted_data):
        fernet = Fernet(self.ENCRYPTION_KEY)
        decrypted_data = fernet.decrypt(encrypted_data).decode()
        return decrypted_data

    def load_remaining_actions(self):
        if os.path.exists(self.TEMP_FILE):
            with open(self.TEMP_FILE, 'rb') as file:
                encrypted_data = file.read()
                decrypted_data = self.decrypt_data(encrypted_data)
                data = json.loads(decrypted_data)
                if data['case_id'] == self.case_id:
                    return data['actions']
        return []

    def save_remaining_actions(self):
        logger.warning("开始保存临时文件")
        logger.warning(self.remaining_actions)
        data = json.dumps({"case_id": self.case_id, "actions": self.remaining_actions})
        encrypted_data = self.encrypt_data(data)
        with open(self.TEMP_FILE, 'wb') as file:
            file.write(encrypted_data)

    def remove_temp_file(self):
        if os.path.exists(self.TEMP_FILE):
            os.remove(self.TEMP_FILE)

    def normalize_action(self, action):
        """忽略大小写以及空格匹配"""
        return action.lower().replace(" ", "")

    def run_main(self, case_id, action_and_num, start_time):
        self.case_id = case_id
        self.remaining_actions = self.load_remaining_actions()
        if not self.remaining_actions:
            self.remaining_actions = action_and_num

        # 显示日志信息
        wx.CallAfter(self.window.add_log_message, f"请按照提示依次执行以下动作:")
        for action, test_num in action_and_num:
            if action == '时间':
                wx.CallAfter(self.window.add_log_message, f"您选择的动作是: {action}，目标测试时间: {test_num} min")
            else:
                wx.CallAfter(self.window.add_log_message, f"您选择的动作是: {action}，目标测试次数: {test_num}")
        for action, test_num in self.remaining_actions:
            action = self.normalize_action(action)
            test_num = int(test_num)
            # 在每个动作开始前更新临时文件
            self.save_remaining_actions()
            # 清除上一个动作的完成状态
            self.action_complete.clear()
            if '时间' in action:
                wx.CallAfter(self.window.add_log_message, f"开始执行监控时间，目标测试时间: {test_num} min")
                threading.Thread(target=self.monitor_time, args=(test_num,)).start()
            elif action == '电源插拔':
                wx.CallAfter(self.window.add_log_message, f"开始执行监控: {action}，目标测试次数: {test_num}")
                threading.Thread(target=self.monitor_power_plug_changes, args=(test_num,)).start()
            elif action.lower() == 'usb插拔':
                wx.CallAfter(self.window.add_log_message, f"开始执行监控: {action}，目标测试次数: {test_num}")
                thread = threading.Thread(target=self.monitor_device_plug_changes, args=(test_num,))
                thread.start()
                # 获取线程ID
                self.msg_loop_thread_id = thread.ident
            elif action == '键盘按键':
                wx.CallAfter(self.window.add_log_message, f"开始执行监控: {action}，目标测试次数: {test_num}")
                threading.Thread(target=self.monitor_keystrokes, args=(test_num,)).start()
            elif action == '锁屏':
                wx.CallAfter(self.window.add_log_message, f"开始执行监控: {action}，目标测试次数: {test_num}")
                thread = threading.Thread(target=self.monitor_lock_screen_changes, args=(test_num,))
                thread.start()
                # 获取线程ID
                self.msg_loop_thread_id = thread.ident
            elif action == '鼠标点击':
                wx.CallAfter(self.window.add_log_message, f"开始执行监控: {action}，目标测试次数: {test_num}")
                threading.Thread(target=self.monitor_mouse_clicks, args=(test_num,)).start()
            elif action == 's3':
                wx.CallAfter(self.window.add_log_message, f"开始执行监控: {action}，目标测试次数: {test_num}")
                threading.Thread(target=self.test_count_s3_sleep_events, args=(start_time, test_num,)).start()
            elif action == 's4':
                wx.CallAfter(self.window.add_log_message, f"开始执行监控: {action}，目标测试次数: {test_num}")
                threading.Thread(target=self.test_count_s4_sleep_events, args=(start_time, test_num,)).start()
            elif action == 's5':
                wx.CallAfter(self.window.add_log_message, f"开始执行监控: {action}，目标测试次数: {test_num}")
                threading.Thread(target=self.test_count_s5_sleep_events, args=(start_time, test_num,)).start()
            elif action == 'restart':
                wx.CallAfter(self.window.add_log_message, f"开始执行监控: {action}，目标测试次数: {test_num}")
                threading.Thread(target=self.test_count_restart_events, args=(start_time, test_num,)).start()
            elif self.KEY_MAPPING.get(action.lower()):
                wx.CallAfter(self.window.add_log_message, f"开始执行监控按键: {action}，目标测试次数: {test_num}")
                threading.Thread(target=self.monitor_keystrokes, args=(test_num, action,)).start()
            # 等待当前监控动作完成
            self.action_complete.wait()
            wx.CallAfter(self.window.add_log_message, f"动作 {action} 完成")
            # 动作完成后，移除已执行的动作并保存
            self.remaining_actions = self.remaining_actions[1:]
            self.save_remaining_actions()

        # 检查是否有剩余的动作
        if not self.remaining_actions:
            logger.warning("所有动作执行完毕，开始删除临时文件")
            self.remove_temp_file()
        logger.warning("所有动作执行完毕，解禁按钮")
        wx.CallAfter(self.window.after_test)

    def on_close(self, event):
        self.save_remaining_actions()
        self.window.Destroy()
        wx.GetApp().ExitMainLoop()


if __name__ == '__main__':
    a = Patvs_Fuction(1, True)
    s3_sleep_count = a.count_s3_sleep_events(start_time='2024/3/19 17:51:50')
    print(f"The system entered S3 sleep state {s3_sleep_count} times.")

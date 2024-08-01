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


class Patvs_Fuction():
    TEMP_FILE = r"D:\PATVS\temp_action_and_num.json"
    ENCRYPTION_KEY = b'JZfpG9N5K4PQoQMtImxPv80DS-D-WPXr9DN0eF7zhR4='  # 32 bytes URL-safe base64-encoded key

    def __init__(self, window, stop_event):
        self.window = window
        self.stop_event = stop_event
        # 读取临时文件
        self.remaining_actions = []
        self.case_id = None
        self.action_complete = threading.Event()

    def monitor_time(self, num_time):
        """
        监控时间
        """
        count = 0
        num_time = num_time * 60
        wx.CallAfter(self.window.add_log_message, f"等待时间: {num_time} 秒")
        while self.stop_event and count < num_time:
            count += 1
            time.sleep(1)
            wx.CallAfter(self.window.add_log_message, f"Running time {count} of ")

    def monitor_power_plug_changes(self, target_cycles):
        """
        监控电源插拔次数
        """
        # battery.percent  # 电量百分比
        # battery.power_plugged  # 是否连接电源
        # battery.secsleft  # 剩余时间（秒），未充电时可用
        plugged_in_last_state = None
        plug_unplug_cycles = 0
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
                    if plug_unplug_cycles == target_cycles:
                        break
            else:
                logger.error("No battery information found")
                break
            time.sleep(1)
        wx.CallAfter(self.window.add_log_message,
                     f"Target power plug/unplug cycles {plug_unplug_cycles} reached. Exiting.")

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
                            logger.info(f'{event.EventID}')
                            logger.info(occurred_time)
                            if total >= target_cycles:
                                break
            if total >= target_cycles:
                wx.CallAfter(self.window.add_log_message, f"Reached target cycles. S3 sleep events: {total}")
            else:
                message = f"您选择的动作是S3，当前已测试 {total} 次，目标次数为 {target_cycles} 次。是否继续测试?"
                wx.CallAfter(self.window.add_log_message, message)
                wx.CallAfter(self.window.show_message_box, message, total)
                while True:  # 设置一个死循环防止用户还未选择是或者否就进入到下一个迭代。
                    time.sleep(0.1)
        finally:
            win32evtlog.CloseEventLog(hand)

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
        flags = win32evtlog.EVENTLOG_BACKWARDS_READ | win32evtlog.EVENTLOG_SEQUENTIAL_READ
        total = 0
        start_time = datetime.datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")

        try:
            while True:
                events = win32evtlog.ReadEventLog(hand, flags, 0)
                if not events:
                    break  # If no more events, break the loop
                for event in events:
                    if event.EventID == 1:
                        event_data = self.get_event_data(event)

                        # 解析 EventData 获取 SleepTime 和 WakeTime
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
                                logger.info(
                                    f'EventID: {event.EventID}, SleepTime: {sleep_time}, WakeTime: {wake_time}')
                                wx.CallAfter(self.window.add_log_message,
                                             f'EventID: {event.EventID}, SleepTime: {sleep_time}, WakeTime: {wake_time}')
                                if total >= target_cycles:
                                    break
        finally:
            win32evtlog.CloseEventLog(hand)

        if total >= target_cycles:
            wx.CallAfter(self.window.add_log_message, f"Reached target cycles. S4 sleep events: {total}")
        else:
            message = f"您选择的动作是S4，当前已测试 {total} 次，目标次数为 {target_cycles} 次。是否继续测试?"
            wx.CallAfter(self.window.add_log_message, message)
            wx.CallAfter(self.window.show_message_box, message, total)
            while True:  # 设置一个死循环防止用户还未选择是或者否就进入到下一个迭代。
                time.sleep(0.1)

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
        start_time = datetime.datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")

        try:
            while True:
                events = win32evtlog.ReadEventLog(hand, flags, 0)
                if not events:
                    break  # If no more events, break the loop
                for event in events:
                    if event.EventID == 7001:
                        occurred_time_str = str(event.TimeGenerated)
                        try:
                            occurred_time = datetime.datetime.strptime(occurred_time_str, "%Y/%m/%d %H:%M:%S")
                        except ValueError:
                            occurred_time = datetime.datetime.strptime(occurred_time_str, "%Y-%m-%d %H:%M:%S")
                        if occurred_time > start_time:
                            total += 1
                            logger.info(f'{event.EventID}')
                            logger.info(occurred_time)
                            if total >= target_cycles:
                                break
        finally:
            win32evtlog.CloseEventLog(hand)

        if total >= target_cycles:
            wx.CallAfter(self.window.add_log_message, f"Reached target cycles. S5 sleep events: {total}")
            wx.CallAfter(self.window.after_test)
        else:
            message = f"您选择的动作是S5，当前已测试 {total} 次，目标次数为 {target_cycles} 次。是否继续测试?"
            wx.CallAfter(self.window.add_log_message, message)
            wx.CallAfter(self.window.show_message_box, message, total)
            while True:  # 设置一个死循环防止用户还未选择是或者否就进入到下一个迭代。
                time.sleep(0.1)

    def test_count_restart_events(self, start_time, target_cycles):
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
                    event_id = event.EventID & 0xFFFF  # 掩码EventID以获取实际值
                    if event_id == 1074:
                        occurred_time_str = str(event.TimeGenerated)
                        try:
                            occurred_time = datetime.datetime.strptime(occurred_time_str, "%Y/%m/%d %H:%M:%S")
                        except ValueError:
                            occurred_time = datetime.datetime.strptime(occurred_time_str, "%Y-%m-%d %H:%M:%S")
                        if occurred_time > start_time:
                            total += 1
                            if total >= target_cycles:
                                break
        finally:
            win32evtlog.CloseEventLog(hand)

        if total >= target_cycles:
            wx.CallAfter(self.window.add_log_message, f"Reached target cycles. ReStart sleep events: {total}")
            wx.CallAfter(self.window.after_test)
        else:
            message = f"您选择的动作是ReStart，当前已测试 {total} 次，目标次数为 {target_cycles} 次。是否继续测试?"
            wx.CallAfter(self.window.add_log_message, message)
            wx.CallAfter(self.window.show_message_box, message, total)
            while True:  # 设置一个死循环防止用户还未选择是或者否就进入到下一个迭代。
                time.sleep(0.1)

    def monitor_device_plug_changes(self, target_cycles):
        notification = Notification(0, target_cycles, self.window)
        notification.messageLoop()
        self.action_complete.set()  # 设置动作完成状态

    def monitor_lock_screen_changes(self, target_cycles):
        monitor_locks(target_cycles, self.window)
        self.action_complete.set()  # 设置动作完成状态

    def monitor_keystrokes(self, target_cycles):
        key_count = 0

        def on_press(key):
            nonlocal key_count
            key_count += 1
            message = (f"Key pressed: {key}. Total count: {key_count}")
            wx.CallAfter(self.window.add_log_message, message)
            if key_count >= target_cycles or not self.stop_event:
                message = ("Reached target keystroke count. Exiting...")
                wx.CallAfter(self.window.add_log_message, message)
                return False  # Stop the listener

        # Collect events until the target keystroke count is reached
        with keyboard.Listener(on_press=on_press) as listener:
            listener.join()

    def monitor_mouse_clicks(self, target_cycles):
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
                    wx.CallAfter(self.window.after_test)
                    return False  # Stop the listener

        # Collect events until the target click count is reached
        with mouse.Listener(on_click=on_click) as listener:
            listener.join()

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
            test_num = int(test_num)
            # 在每个动作开始前更新临时文件
            self.save_remaining_actions()
            # 清除上一个动作的完成状态
            self.action_complete.clear()
            if action == '时间':
                wx.CallAfter(self.window.add_log_message, f"开始执行监控时间，目标测试时间: {test_num} min")
                self.monitor_time(test_num)
                self.action_complete.set()  # 设置动作完成状态
            elif action == '电源插拔':
                wx.CallAfter(self.window.add_log_message, f"开始执行监控: {action}，目标测试次数: {test_num}")
                self.monitor_power_plug_changes(test_num)
                self.action_complete.set()  # 设置动作完成状态
            elif action == 'USB插拔':
                wx.CallAfter(self.window.add_log_message, f"开始执行监控: {action}，目标测试次数: {test_num}")
                threading.Thread(target=self.monitor_device_plug_changes, args=(test_num,)).start()
            elif action == '键盘按键':
                wx.CallAfter(self.window.add_log_message, f"开始执行监控: {action}，目标测试次数: {test_num}")
                self.monitor_keystrokes(test_num)
            elif action == '锁屏':
                wx.CallAfter(self.window.add_log_message, f"开始执行监控: {action}，目标测试次数: {test_num}")
                threading.Thread(target=self.monitor_lock_screen_changes, args=(test_num,)).start()
            elif action == '鼠标点击':
                wx.CallAfter(self.window.add_log_message, f"开始执行监控: {action}，目标测试次数: {test_num}")
                self.monitor_mouse_clicks(test_num)
            elif action == 'S3':
                wx.CallAfter(self.window.add_log_message, f"开始执行监控: {action}，目标测试次数: {test_num}")
                self.test_count_s3_sleep_events(start_time, test_num)
                self.action_complete.set()  # 设置动作完成状态
            elif action == 'S4':
                wx.CallAfter(self.window.add_log_message, f"开始执行监控: {action}，目标测试次数: {test_num}")
                self.test_count_s4_sleep_events(start_time, test_num)
                self.action_complete.set()  # 设置动作完成状态
            elif action == 'S5':
                wx.CallAfter(self.window.add_log_message, f"开始执行监控: {action}，目标测试次数: {test_num}")
                self.test_count_s5_sleep_events(start_time, test_num)
                self.action_complete.set()  # 设置动作完成状态
            elif action == 'Restart':
                wx.CallAfter(self.window.add_log_message, f"开始执行监控: {action}，目标测试次数: {test_num}")
                self.test_count_restart_events(start_time, test_num)
                self.action_complete.set()  # 设置动作完成状态

            # 等待当前监控动作完成
            self.action_complete.wait()
            wx.CallAfter(self.window.add_log_message, f"动作 {action} 完成")
            # 动作完成后，移除已执行的动作并保存
            self.remaining_actions = self.remaining_actions[1:]
            self.save_remaining_actions()

        # 检查是否有剩余的动作
        if not self.remaining_actions:
            self.remove_temp_file()

        wx.CallAfter(self.window.after_test)

    def on_close(self, event):
        self.save_remaining_actions()
        self.window.Destroy()
        wx.GetApp().ExitMainLoop()


if __name__ == '__main__':
    a = Patvs_Fuction(1, True)
    s3_sleep_count = a.count_s3_sleep_events(start_time='2024/3/19 17:51:50')
    print(f"The system entered S3 sleep state {s3_sleep_count} times.")

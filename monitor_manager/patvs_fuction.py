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


class Patvs_Fuction():
    def __init__(self, window, stop_event):
        self.window = window
        self.stop_event = stop_event

    def monitor_time(self, num_time, test_num):
        """
        监控时间
        """
        for i in range(test_num):
            count = 0
            wx.CallAfter(self.window.add_log_message, f"执行总次数:{test_num}, 每次时间{num_time}S, 开始执行第{i+1}次")
            while self.stop_event and count < num_time:
                count += 1
                time.sleep(1)
                logger.info(f"Running time {count} of ")
                wx.CallAfter(self.window.add_log_message, f"Running time {count} of ")
        wx.CallAfter(self.window.after_test)

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
        return plug_unplug_cycles

    def start_monitoring_power(self, target_cycles):
        plug_unplug_cycles = self.monitor_power_plug_changes(target_cycles)
        wx.CallAfter(self.window.after_test)
        message = (f"Target power plug/unplug cycles {plug_unplug_cycles} reached. Exiting.")
        wx.CallAfter(self.window.add_log_message, message)

    def count_s3_sleep_events(self, start_time):
        hand = win32evtlog.OpenEventLog(None, "System")
        # 从新到旧读取
        flags = win32evtlog.EVENTLOG_BACKWARDS_READ | win32evtlog.EVENTLOG_SEQUENTIAL_READ
        total = 0
        start_time = datetime.datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
        try:
            # Read the events
            events = win32evtlog.ReadEventLog(hand, flags, 0)
            while self.stop_event and events:
                for event in events:
                    if event.EventID == 507 or event.EventID == 107:
                        occurred_time_str = str(event.TimeGenerated)
                        try:
                            occurred_time = datetime.datetime.strptime(occurred_time_str, "%Y/%m/%d %H:%M:%S")
                        except ValueError:
                            occurred_time = datetime.datetime.strptime(occurred_time_str, "%Y-%m-%d %H:%M:%S")
                        if occurred_time > start_time:
                            total += 1
                            message = (f"S3 cycle completed: {total} times")
                            wx.CallAfter(self.window.add_log_message, message)
                events = win32evtlog.ReadEventLog(hand, flags, 0)
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
        finally:
            win32evtlog.CloseEventLog(hand)

        if total >= target_cycles:
            message = f"Reached target cycles. S3 sleep events: {total}"
            wx.CallAfter(self.window.add_log_message, message)
            wx.CallAfter(self.window.after_test)
        else:
            message = f"您选择的动作是S3，当前已测试 {total} 次，目标次数为 {target_cycles} 次。是否继续测试?"
            wx.CallAfter(self.window.add_log_message, message)
            wx.CallAfter(self.window.show_message_box, message, total)

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
                                wx.CallAfter(self.window.add_log_message, f'EventID: {event.EventID}, SleepTime: {sleep_time}, WakeTime: {wake_time}')
                                if total >= target_cycles:
                                    break
        finally:
            win32evtlog.CloseEventLog(hand)

        if total >= target_cycles:
            message = f"Reached target cycles. S4 sleep events: {total}"
            wx.CallAfter(self.window.add_log_message, message)
            wx.CallAfter(self.window.after_test)
        else:
            message = f"您选择的动作是S4，当前已测试 {total} 次，目标次数为 {target_cycles} 次。是否继续测试?"
            wx.CallAfter(self.window.add_log_message, message)
            wx.CallAfter(self.window.show_message_box, message, total)

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
            message = f"Reached target cycles. S5 sleep events: {total}"
            wx.CallAfter(self.window.add_log_message, message)
            wx.CallAfter(self.window.after_test)
        else:
            message = f"您选择的动作是S5，当前已测试 {total} 次，目标次数为 {target_cycles} 次。是否继续测试?"
            wx.CallAfter(self.window.add_log_message, message)
            wx.CallAfter(self.window.show_message_box, message, total)

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
            message = f"Reached target cycles. ReStart sleep events: {total}"
            wx.CallAfter(self.window.add_log_message, message)
            wx.CallAfter(self.window.after_test)
        else:
            message = f"您选择的动作是ReStart，当前已测试 {total} 次，目标次数为 {target_cycles} 次。是否继续测试?"
            wx.CallAfter(self.window.add_log_message, message)
            wx.CallAfter(self.window.show_message_box, message, total)

    def monitor_device_plug_changes(self, target_cycles):
        notification = Notification(0, target_cycles, self.window)
        notification.messageLoop()
        wx.CallAfter(self.window.after_test)

    def monitor_lock_screen_changes(self, target_cycles):
        monitor_locks(target_cycles, self.window)
        wx.CallAfter(self.window.after_test)

    def s3_and_device_plug_changes(self, target_cycles):
        # 设定开始时间为当前时间
        start_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        logger.info(f"Monitoring started at {start_time}")

        device_unplug_cycles = 0
        s3_sleep_events = 0

        while device_unplug_cycles < target_cycles or s3_sleep_events < target_cycles:
            if device_unplug_cycles < target_cycles:
                device_unplug_cycles = self.monitor_device_plug_changes(target_cycles - device_unplug_cycles)

            if s3_sleep_events < target_cycles:
                s3_sleep_events = self.count_s3_sleep_events(start_time=start_time)

            # 两个都达到目标次数后退出循环
            if device_unplug_cycles >= target_cycles and s3_sleep_events >= target_cycles:
                break
            elif not self.stop_event:
                break
            time.sleep(1)
        message = (
            f"Reached target cycles. Plug/unplug cycles: {device_unplug_cycles}, S3 sleep events: {s3_sleep_events}")
        wx.CallAfter(self.window.add_log_message, message)
        wx.CallAfter(self.window.after_test)

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
                wx.CallAfter(self.window.after_test)
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


if __name__ == '__main__':
    a = Patvs_Fuction(1, True)
    s3_sleep_count = a.count_s3_sleep_events(start_time='2024/3/19 17:51:50')
    print(f"The system entered S3 sleep state {s3_sleep_count} times.")

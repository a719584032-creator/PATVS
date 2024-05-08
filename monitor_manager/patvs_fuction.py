# -*- coding: utf-8 -*-
# 负责监控逻辑
import wx
from common.logs import logger
from monitor_manager.devicerm import Notification
from sql_manager.patvs_sql import Patvs_SQL
import time
import psutil
import win32evtlog
import pywintypes
import win32evtlogutil
import win32con
import pytz
import datetime


class Patvs_Fuction():
    def __init__(self, window, stop_event):
        self.window = window
        self.stop_event = stop_event

    def monitor_time(self, num):
        """
        监控时间
        """
        count = 0
        message = (f"please waiting {num}S")
        wx.CallAfter(self.window.add_log_message, message)
        while self.stop_event and count < num:
            count += 1
            time.sleep(1)
            logger.info(f"Running time {count} of ")
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

    def test_count_s4_sleep_events(self, start_time, target_cycles):
        hand = win32evtlog.OpenEventLog(None, "System")
        flags = win32evtlog.EVENTLOG_BACKWARDS_READ | win32evtlog.EVENTLOG_SEQUENTIAL_READ
        total = 0
        start_time = datetime.datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
        try:
            events = win32evtlog.ReadEventLog(hand, flags, 0)
            while self.stop_event and total < target_cycles:
                for event in events:
                    if event.EventID == 1:
                        occurred_time_str = str(event.TimeGenerated)
                        try:
                            occurred_time = datetime.datetime.strptime(occurred_time_str, "%Y/%m/%d %H:%M:%S")
                        except ValueError:
                            occurred_time = datetime.datetime.strptime(occurred_time_str, "%Y-%m-%d %H:%M:%S")
                        if occurred_time > start_time:
                            total += 1
                            logger.info(f'{event.EventID}')
                            logger.info(occurred_time)
                            message = f"S4 cycle completed: {total} times"
                            wx.CallAfter(self.window.add_log_message, message)
                            if total >= target_cycles:
                                break
                if total < target_cycles:
                    events = win32evtlog.ReadEventLog(hand, flags, 0)
                else:
                    break
        finally:
            win32evtlog.CloseEventLog(hand)
        message = (
            f"Reached target cycles. S4 sleep events: {total}")
        wx.CallAfter(self.window.add_log_message, message)
        wx.CallAfter(self.window.after_test)

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
            events = win32evtlog.ReadEventLog(hand, flags, 0)
            while self.stop_event and total < target_cycles:
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
                            message = f"S5 cycle completed: {total} times"
                            wx.CallAfter(self.window.add_log_message, message)
                            if total >= target_cycles:
                                break
                if total < target_cycles:
                    events = win32evtlog.ReadEventLog(hand, flags, 0)
                else:
                    break
        finally:
            win32evtlog.CloseEventLog(hand)
        message = (
            f"Reached target cycles. S5 sleep events: {total}")
        wx.CallAfter(self.window.add_log_message, message)
        wx.CallAfter(self.window.after_test)

    def monitor_device_plug_changes(self, target_cycles):
        notification = Notification(target_cycles, self.window)
        notification.messageLoop()
        wx.CallAfter(self.window.after_test)
        return target_cycles
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



if __name__ == '__main__':
    a = Patvs_Fuction(1)
    s3_sleep_count = a.count_s3_sleep_events(start_time='2024/3/19 17:51:50')
    print(f"The system entered S3 sleep state {s3_sleep_count} times.")

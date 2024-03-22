# -*- coding: utf-8 -*-
# 负责监控逻辑
import wx
from common.logs import logger
import time
import psutil

class Patvs_Fuction():
    def __init__(self, window):
        self.window = window

    def monitor_time(self, num):
        """
        监控时间
        """
        count = 0
        message = (f"please waiting {num}S")
        wx.CallAfter(self.window.add_log_message, message)
        while count < num:
            count += 1
            time.sleep(1)
            logger.info(f"Running time {count} of ")
        wx.CallAfter(self.window.after_test)

    def monitor_power_plug_changes(self, target_cycles, interval=1):
        """
        监控电源插拔次数
        """
        # battery.percent  # 电量百分比
        # battery.power_plugged  # 是否连接电源
        # battery.secsleft  # 剩余时间（秒），未充电时可用
        plugged_in_last_state = None
        plug_unplug_cycles = 0

        while plug_unplug_cycles < target_cycles:
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
                        message = (f"Power plug/unplug cycle completed: {plug_unplug_cycles} times")
                        wx.CallAfter(self.window.add_log_message, message)
                    if plug_unplug_cycles == target_cycles:
                        break
            else:
                logger.error("No battery information found")
                break
            time.sleep(interval)
        wx.CallAfter(self.window.after_test)
        message = (f"Target power plug/unplug cycles {target_cycles} reached. Exiting.")
        wx.CallAfter(self.window.add_log_message, message)
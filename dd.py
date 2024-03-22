import psutil
import time


# percent = battery.percent  # 电量百分比
# plugged = battery.power_plugged  # 是否连接电源
# time_left = battery.secsleft  # 剩余时间（秒），未充电时可用

def monitor_power_plug_changes(target_cycles, interval=1):
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
                    print(f"Power plug/unplug cycle completed: {plug_unplug_cycles} times")
                if plug_unplug_cycles == target_cycles:
                    break
        else:
            print("No battery information found")
            break
        time.sleep(interval)

    print(f"Target power plug/unplug cycles {target_cycles} reached. Exiting.")


# 调用函数，设置目标周期次数
num = 3  # 设置监测的目标周期次数
monitor_power_plug_changes(num)
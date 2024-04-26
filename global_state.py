# global_state.py

# 初始化全局状态变量
stop_event_triggered = False


def set_stop_event(state):
    global stop_event_triggered
    stop_event_triggered = state


def get_stop_event():
    global stop_event_triggered
    return stop_event_triggered

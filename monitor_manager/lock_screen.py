# -*- coding: utf-8 -*-
# 检测电脑锁屏事件
import ctypes
import win32api
import win32con
import win32gui
import win32ts
import uuid
import wx
from common.logs import logger

# 定义WM_WTSSESSION_CHANGE常量的值
WM_WTSSESSION_CHANGE = 0x2B1

WTS_SESSION_LOCK = 0x7
WTS_SESSION_UNLOCK = 0x8


class WTSSESSION_NOTIFICATION(ctypes.Structure):
    _fields_ = [("cbSize", ctypes.c_uint),
                ("dwSessionId", ctypes.c_uint)]


class SessionNotificationHandler:
    def __init__(self, target_cycles, window):
        self.hwnd = None
        self.window = window
        self.className = f"suopin_WindowClass_{uuid.uuid4()}"
        self.target_cycles = target_cycles
        self.lock_count = 0
        wc = win32gui.WNDCLASS()
        wc.lpfnWndProc = self.wnd_proc
        wc.lpszClassName = self.className
        self.class_atom = win32gui.RegisterClass(wc)
        self.hwnd = win32gui.CreateWindow(self.class_atom,
                                          self.className,
                                          0,
                                          0, 0, 0, 0,
                                          0, 0, 0, None)
        win32ts.WTSRegisterSessionNotification(self.hwnd, win32ts.NOTIFY_FOR_THIS_SESSION)

    def wnd_proc(self, hwnd, msg, wparam, lparam):
        if msg == WM_WTSSESSION_CHANGE:  # 使用自定义的常量
            if wparam == WTS_SESSION_LOCK:
                self.lock_count += 1
                logger.info(f"Session is locked. Lock count: {self.lock_count}")
                wx.CallAfter(self.window.add_log_message, f"Session is locked. Lock count: {self.lock_count}")
                if self.lock_count >= self.target_cycles:
                    logger.info(f"Target lock count {self.target_cycles} reached. Exiting...")
                    wx.CallAfter(self.window.add_log_message,
                                 f"Target lock count {self.target_cycles} reached. Exiting...")
                    win32ts.WTSUnRegisterSessionNotification(self.hwnd)
                    win32gui.DestroyWindow(self.hwnd)
                    win32gui.PostQuitMessage(0)
            elif wparam == WTS_SESSION_UNLOCK:
                logger.info("Session is unlocked.")
                wx.CallAfter(self.window.add_log_message, "Session is unlocked.")
        return win32gui.DefWindowProc(hwnd, msg, wparam, lparam)

    def run(self):
        wx.CallAfter(self.window.add_log_message, "Monitoring session lock/unlock events...")
        try:
            win32gui.PumpMessages()
        except KeyboardInterrupt:
            logger.warning("Monitoring stopped.")
            wx.CallAfter(self.window.add_log_message, "Monitoring stopped.")
            win32ts.WTSUnRegisterSessionNotification(self.hwnd)
            win32gui.DestroyWindow(self.hwnd)
            win32gui.UnregisterClass(self.class_atom, None)
        except Exception as e:
            logger.error(f"未知错误 {e}")


def monitor_locks(target_cycles, window):
    handler = SessionNotificationHandler(target_cycles, window)
    handler.run()

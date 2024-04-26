# -*- coding: utf-8 -*-
# 检测设备热插拔事件 并在控制台输出 ，依赖库 pywin32
# WinApi 参考文档 http://www.yfvb.com/help/win32sdk/    https://timgolden.me.uk/pywin32-docs/contents.html
import win32con
import win32gui
import win32api
import win32gui_struct
from datetime import datetime
import wx
import pywintypes
import winerror
import time
from common.logs import logger
import global_state

GUID_DEVINTERFACE_USB_DEVICE = "{A5DCBF10-6530-11D2-901F-00C04FB951ED}"


class Notification:
    # 创建注册窗口并接收消息通知
    def __init__(self, target_cycles, window):
        self.target_cycles = target_cycles  # 目标的插拔次数
        self.cycles_count = 0
        self.window = window
        message_map = {
            win32con.WM_DEVICECHANGE: self.onDeviceChange
        }
        wc = win32gui.WNDCLASS()
        """
        WNDCLASS结构包含由RegisterClass函数注册的窗口类属性。

        typedef struct _WNDCLASS { // wc
        UINT style;
        WNDPROC lpfnWndProc;
        int cbClsExtra;
        int cbWndExtra;
        HANDLE hInstance;
        HICON hIcon;
        HCURSOR hCursor;
        HBRUSH hbrBackground;
        LPCTSTR lpszMenuName;
        LPCTSTR lpszClassName;
        } WNDCLASS;
        """
        wc.hInstance = win32api.GetModuleHandle(None)
        """
        如果文件已被映射到调用进程的地址空间，GetModuleHandle函数将返回指定模块的模块句柄。
        返回值
        如果函数成功，则返回值是指定模块的句柄。
        如果函数失败，返回值为NULL。要获取扩展错误信息，请调用GetLastError.
        """
        wc.lpszClassName = "DeviceChange_WindowClass"
        wc.style = win32con.CS_VREDRAW | win32con.CS_HREDRAW
        wc.lpfnWndProc = message_map
        try:
            classAtom = win32gui.RegisterClass(wc)
        except pywintypes.error as e:
            # 如果类已注册, 忽略错误，获取已注册的类
            if e.winerror == winerror.ERROR_CLASS_ALREADY_EXISTS:
                pass
            else:
                raise
        """
        RegisterClass函数注册一个窗口类，用于随后在CreateWindow或CreateWindowEx函数的调用中使用。
        参数
        【lpWndClass】
        指向WNDCLASS结构。在将结构传递给函数之前，必须使用适当的类属性来填充结构。
        返回值
        如果函数成功，则返回值是唯一标识正在注册的类的原子。
        如果函数失败，返回值为零。要获取扩展错误信息，请调用GetLastError.
        """
        style = win32con.WS_OVERLAPPED | win32con.WS_SYSMENU
        self.hwnd = win32gui.CreateWindow("DeviceChange_WindowClass", "Device Change", style, 0, 0,
                                          win32con.CW_USEDEFAULT,
                                          win32con.CW_USEDEFAULT, 0, 0, wc.hInstance, None)
        """
        CreateWindow函数创建一个重叠的弹出窗口或子窗口。它指定窗口类，窗口标题，窗口样式和（可选）窗口的初始位置和大小。该函数还指定窗口的父项或所有者（如果有）以及窗口的菜单。

        HWND CreateWindow ( 
        LPCTSTR 【lpClassName】,	//指向注册类名的指针
        LPCTSTR 【lpWindowName】,	//指向窗口名称的指针
        DWORD 【dwStyle】,	//窗口样式
        INT 【x】,	//窗口的水平位置
        INT 【y】,	//窗口的垂直位置
        INT 【nWidth】,	//窗口宽度
        INT 【nHeight参数】,	//窗口高度
        HWND 【hWndParent】,	//处理父或所有者窗口
        HMENU 【HMENU】,	//处理菜单或子窗口标识符
        HANDLE 【的hInstance】,	//处理应用程序实例
        LPVOID 【// pointer to window-creation data】	//指向窗口创建数据的指针
        );
        """
        dbt_dev_broadcast_deviceinterface = win32gui_struct.PackDEV_BROADCAST_DEVICEINTERFACE(
            GUID_DEVINTERFACE_USB_DEVICE)
        # 生成设备 GUID
        self.hdn = win32gui.RegisterDeviceNotification(self.hwnd, dbt_dev_broadcast_deviceinterface,
                                                       win32con.DEVICE_NOTIFY_WINDOW_HANDLE)
        """
        注册窗口将接收通知的设备或设备类型。
        handle : PyHANDLE
        The handle to a window or a service
        filter : buffer
        A buffer laid out like one of the DEV_BROADCAST_* structures, generally built by one of the win32gui_struct helpers.
        flags : int
        """

    def onDeviceChange(self, hwnd, message, wparam, lparam):
        dbch = win32gui_struct.UnpackDEV_BROADCAST(lparam)

        if wparam == win32con.DBT_DEVICEREMOVECOMPLETE:
            print(f"设备{dbch.name}已断开连接，当前时间:{datetime.now()}")
            self.cycles_count += 1
            message = f"设备{dbch.name}已断开连接，当前次数:{self.cycles_count}"
            wx.CallAfter(self.window.add_log_message, message)
        elif wparam == win32con.DBT_DEVICEARRIVAL:
            print(f"设备{dbch.name}已连接，当前时间:{datetime.now()}")
            message = f"设备{dbch.name}已连接，当前次数:{self.cycles_count}"
            wx.CallAfter(self.window.add_log_message, message)
        # 检查是否达到目标的插拔次数，如果是的话结束消息循环
        if self.cycles_count >= self.target_cycles:
            message = f"Device plug/unplug cycle completed: {self.cycles_count} times"
            wx.CallAfter(self.window.add_log_message, message)
            win32gui.PostQuitMessage(0)

        return 1

    def messageLoop(self):
        win32gui.PumpMessages()
        """
        运行消息循环，直到收到WM_QUIT消息
        Return Value
        当收到WM_QUIT消息时，从PostQuitMessage返回退出代码
        """

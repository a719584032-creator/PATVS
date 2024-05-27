import ctypes
import win32api
import win32con
import win32gui
import win32ts

# 定义WM_WTSSESSION_CHANGE常量的值
WM_WTSSESSION_CHANGE = 0x2B1

WTS_SESSION_LOCK = 0x7
WTS_SESSION_UNLOCK = 0x8

class WTSSESSION_NOTIFICATION(ctypes.Structure):
    _fields_ = [("cbSize", ctypes.c_uint),
                ("dwSessionId", ctypes.c_uint)]

class SessionNotificationHandler:
    def __init__(self):
        self.hwnd = None
        self.className = "SessionNotificationHandler"
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
                print("Session is locked.")
            elif wparam == WTS_SESSION_UNLOCK:
                print("Session is unlocked.")
        return win32gui.DefWindowProc(hwnd, msg, wparam, lparam)

    def run(self):
        print("Monitoring session lock/unlock events... Press Ctrl+C to exit.")
        try:
            win32gui.PumpMessages()
        except KeyboardInterrupt:
            print("Monitoring stopped.")
            win32ts.WTSUnRegisterSessionNotification(self.hwnd)
            win32gui.DestroyWindow(self.hwnd)
            win32gui.UnregisterClass(self.class_atom, None)

if __name__ == "__main__":
    handler = SessionNotificationHandler()
    handler.run()

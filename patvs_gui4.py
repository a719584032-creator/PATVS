# -*- coding: utf-8 -*-

import wx
import win32api
import sys, os

APP_TITLE = u'动态布局'
APP_ICON = 'icon/PATS.ico'


class mainFrame(wx.Frame):
    '''程序主窗口类，继承自wx.Frame'''

    def __init__(self, parent):
        '''构造函数'''

        wx.Frame.__init__(self, parent, -1, APP_TITLE)
        self.SetBackgroundColour(wx.Colour(240, 240, 240))
        self.SetSize((800, 600))
        self.Center()

        if hasattr(sys, "frozen") and getattr(sys, "frozen") == "windows_exe":
            exeName = win32api.GetModuleFileName(win32api.GetModuleHandle(None))
            icon = wx.Icon(exeName, wx.BITMAP_TYPE_ICO)
        else:
            icon = wx.Icon(APP_ICON, wx.BITMAP_TYPE_ICO)
        self.SetIcon(icon)

        preview = wx.Panel(self, -1, style=wx.SUNKEN_BORDER)
        preview.SetBackgroundColour(wx.Colour(0, 0, 0))
        btn_capture = wx.Button(self, -1, u'拍照', size=(100, -1))
        btn_up = wx.Button(self, -1, u'↑', size=(30, 30))
        btn_down = wx.Button(self, -1, u'↓', size=(30, 30))
        btn_left = wx.Button(self, -1, u'←', size=(30, 30))
        btn_right = wx.Button(self, -1, u'→', size=(30, 30))
        tc = wx.TextCtrl(self, -1, '', style=wx.TE_MULTILINE)

        sizer_arrow_mid = wx.BoxSizer()
        sizer_arrow_mid.Add(btn_left, 0, wx.RIGHT, 16)
        sizer_arrow_mid.Add(btn_right, 0, wx.LEFT, 16)

        # sizer_arrow = wx.BoxSizer(wx.VERTICAL)
        sizer_arrow = wx.StaticBoxSizer(wx.StaticBox(self, -1, u'方向键'), wx.VERTICAL)
        sizer_arrow.Add(btn_up, 0, wx.ALIGN_CENTER | wx.ALL, 0)
        sizer_arrow.Add(sizer_arrow_mid, 0, wx.TOP | wx.BOTTOM, 1)
        sizer_arrow.Add(btn_down, 0, wx.ALIGN_CENTER | wx.ALL, 0)

        sizer_right = wx.BoxSizer(wx.VERTICAL)
        sizer_right.Add(btn_capture, 0, wx.ALL, 20)
        sizer_right.Add(sizer_arrow, 0, wx.ALIGN_CENTER | wx.ALL, 0)
        sizer_right.Add(tc, 1, wx.ALL, 10)

        sizer_max = wx.BoxSizer()
        sizer_max.Add(preview, 1, wx.EXPAND | wx.LEFT | wx.TOP | wx.BOTTOM, 5)
        sizer_max.Add(sizer_right, 0, wx.EXPAND | wx.ALL, 0)

        # 将动态布局加到窗口上并重新布局
        self.SetAutoLayout(True)
        self.SetSizer(sizer_max)
        self.Layout()


class mainApp(wx.App):
    def OnInit(self):
        self.SetAppName(APP_TITLE)
        self.Frame = mainFrame(None)
        self.Frame.Show()
        return True


if __name__ == "__main__":
    app = mainApp()
    app.MainLoop()

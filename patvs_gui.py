# -*- coding: utf-8 -*-
# 负责主界面展示
import wx
from ui_manager.patvs_ui_manager import TestCasesPanel
import sys


class MainApp(wx.App):
    def OnInit(self):
        frame = MainWindow(None, title="PATVS-1.0.0")
        self.SetTopWindow(frame)
        frame.Show(True)
        return True

class MainWindow(wx.Frame):
    def __init__(self, parent, title):
        super(MainWindow, self).__init__(parent, title=title, size=(1000, 700))

        # 添加 TestCasesPanel
        self.panel = TestCasesPanel(self)
        self.Bind(wx.EVT_CLOSE, self.on_close)
        self.Centre()


    def on_close(self, event):
        self.panel.save_state()  # 调用 TestCasesPanel 类的保存状态方法
        self.Destroy()


if __name__ == "__main__":
    app = MainApp(redirect=False)
    app.MainLoop()
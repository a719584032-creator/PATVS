# -*- coding: utf-8 -*-
import time

import wx


class TestFrame(wx.Frame):
    def __init__(self, *args, **kw):
        super(TestFrame, self).__init__(*args, **kw)
        self.panel = wx.Panel(self)
        self.InitUI()

    def InitUI(self):


        vbox = wx.BoxSizer(wx.VERTICAL)

        # 监控动作下拉框
        self.monitor_action_combo = wx.ComboBox(self.panel, choices=["", "S3", "S4", "S5", "Restart"], style=wx.CB_READONLY)
        vbox.Add(wx.StaticText(self.panel, label="监控动作"), flag=wx.ALL, border=5)
        vbox.Add(self.monitor_action_combo, flag=wx.EXPAND | wx.ALL, border=5)

        # 测试次数下拉框
        self.test_count_combo = wx.ComboBox(self.panel, choices=["", "1", "3", "5", "10", "20", "50", "100"],
                                            style=wx.CB_READONLY)
        vbox.Add(wx.StaticText(self.panel, label="测试次数"), flag=wx.ALL, border=5)
        vbox.Add(self.test_count_combo, flag=wx.EXPAND | wx.ALL, border=5)

        # 按钮
        self.start_button = wx.Button(self.panel, label="Start")
        self.pass_button = wx.Button(self.panel, label="Pass")
        self.fail_button = wx.Button(self.panel, label="Fail")
        self.block_button = wx.Button(self.panel, label="Block")

        vbox.Add(self.start_button, flag=wx.ALL, border=5)
        vbox.Add(self.pass_button, flag=wx.ALL, border=5)
        vbox.Add(self.fail_button, flag=wx.ALL, border=5)
        vbox.Add(self.block_button, flag=wx.ALL, border=5)

        # 设置按钮初始状态
        self.pass_button.Hide()
        self.fail_button.Hide()
        self.block_button.Hide()

        self.start_button.Bind(wx.EVT_BUTTON, self.OnStart)
        self.pass_button.Bind(wx.EVT_BUTTON, self.OnPass)
        self.fail_button.Bind(wx.EVT_BUTTON, self.OnFail)
        self.block_button.Bind(wx.EVT_BUTTON, self.OnBlock)

        self.panel.SetSizer(vbox)

    def OnStart(self, event):
        monitor_action = self.monitor_action_combo.GetValue()
        test_count = self.test_count_combo.GetValue()

        if not monitor_action or not test_count:
            wx.MessageBox("监控动作/测试次数不能为空", "错误", wx.OK | wx.ICON_ERROR)
        else:
            self.start_button.Hide()
            self.pass_button.Show()
            self.fail_button.Show()
            self.block_button.Show()
            self.pass_button.Disable()
            self.fail_button.Disable()
            self.block_button.Disable()
            self.panel.Layout()
            # 调用对应的测试函数，这里仅作示例
            if monitor_action == "S3":
                while self.test_S3() < int(test_count):
                    time.sleep(5)
                print("解禁按钮")
                self.pass_button.Enable()
                self.fail_button.Enable()
                self.block_button.Enable()
                self.panel.Layout()

            # 依次调用其他函数...

            # 测试开始后，更改按钮状态

    def test_S3(self):
        # 测试S3的逻辑
        # 此处仅为示意，实际逻辑应根据需求实现
        n = 1
        while n < 10:
            n += 1
            time.sleep(1)
        return n

    def OnPass(self, event):
        self.ResetButtons()

    def OnFail(self, event):
        self.ResetButtons()

    def OnBlock(self, event):
        self.ResetButtons()

    def ResetButtons(self):
        # 重置按钮状态
        self.pass_button.Hide()
        self.fail_button.Hide()
        self.block_button.Hide()
        self.start_button.Show()
        self.panel.Layout()


def main():
    app = wx.App(False)
    frame = TestFrame(None, title="测试程序", size=(300, 400))
    frame.Show()
    app.MainLoop()


if __name__ == "__main__":
    main()

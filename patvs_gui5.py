# -*- coding: utf-8 -*-
import wx
import threading
import time

class TestFrame(wx.Frame):
    def __init__(self, *args, **kw):
        super(TestFrame, self).__init__(*args, **kw)

        # Initialize UI
        self.InitUI()

    def InitUI(self):
        panel = wx.Panel(self)

        self.startBtn = wx.Button(panel, label="Start", pos=(20, 20))
        self.passBtn = wx.Button(panel, label="Pass", pos=(20, 70))
        self.failBtn = wx.Button(panel, label="Fail", pos=(120, 70))
        self.blockBtn = wx.Button(panel, label="Block", pos=(220, 70))
        self.logTxtCtrl = wx.TextCtrl(panel, pos=(20, 120), size=(280, 60), style=wx.TE_MULTILINE|wx.TE_READONLY)

        # Bind events
        self.startBtn.Bind(wx.EVT_BUTTON, self.OnStart)
        self.passBtn.Bind(wx.EVT_BUTTON, lambda evt, lbl="Pass": self.OnTestResult(evt, lbl))
        self.failBtn.Bind(wx.EVT_BUTTON, lambda evt, lbl="Fail": self.OnTestResult(evt, lbl))
        self.blockBtn.Bind(wx.EVT_BUTTON, self.OnBlock)

        # Initially disable Pass and Fail buttons
        self.passBtn.Disable()
        self.failBtn.Disable()

    def OnStart(self, event):
        self.logTxtCtrl.SetValue("Testing started... Please perform the system test.")
        self.passBtn.Disable()
        self.failBtn.Disable()
        self.startBtn.Disable()

        # Start test function in a new thread to avoid freezing the UI
        threading.Thread(target=self.TestFunction).start()

    def TestFunction(self):
        # Simulate long-running task
        time.sleep(30)  # Wait for 1 minute

        # Re-enable Pass and Fail buttons after the wait
        wx.CallAfter(self.passBtn.Enable)
        wx.CallAfter(self.failBtn.Enable)
        wx.CallAfter(self.startBtn.Enable)
        wx.CallAfter(self.logTxtCtrl.SetValue, "Testing completed. Please select Pass or Fail.")

    def OnTestResult(self, event, label):
        with open("test.txt", "a") as file:
            file.write(f"{label}\n")
        self.logTxtCtrl.SetValue(f"Result: {label} recorded")

    def OnBlock(self, event):
        with open("test.txt", "a") as file:
            file.write("Block\n")
        self.logTxtCtrl.SetValue("Testing blocked")

        # If needed, stop the running test function
        # Note: Implementing a safe stop might require more complex handling, depending on the actual test function

def main():
    app = wx.App(False)
    frame = TestFrame(None, title="Test Buttons", size=(340, 220))
    frame.Show()
    app.MainLoop()

if __name__ == "__main__":
    main()

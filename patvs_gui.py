# -*- coding: utf-8 -*-
# 负责主界面展示
import wx
from ui_manager.patvs_ui_manager import TestCasesPanel
from ui_manager.patvs_admin_ui_manager import TestAdminPanel
from common.logs import logger
import sys
import os
from requests_manager.http_requests_manager import http_manager
import json
import base64


def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)


class LoginDialog(wx.Dialog):
    def __init__(self, parent, title):
        super(LoginDialog, self).__init__(parent, title=title, size=(1000, 700))
        self.panel = wx.Panel(self)
        self.sizer = wx.BoxSizer(wx.VERTICAL)

        self.username_label = wx.StaticText(self.panel, label="Username:")
        self.username_text = wx.TextCtrl(self.panel, size=(200, -1))

        self.password_label = wx.StaticText(self.panel, label="Password:")
        self.password_text = wx.TextCtrl(self.panel, style=wx.TE_PASSWORD, size=(200, -1))

        self.remember_me_checkbox = wx.CheckBox(self.panel, label="Remember me")

        self.login_button = wx.Button(self.panel, label="Login")
        self.login_button.Bind(wx.EVT_BUTTON, self.on_login)

        self.change_password_button = wx.Button(self.panel, label="Change Password")
        self.change_password_button.Bind(wx.EVT_BUTTON, self.on_change_password)

        self.sizer.Add(self.username_label, 0, wx.ALL | wx.CENTER, 5)
        self.sizer.Add(self.username_text, 0, wx.ALL | wx.CENTER, 5)
        self.sizer.Add(self.password_label, 0, wx.ALL | wx.CENTER, 5)
        self.sizer.Add(self.password_text, 0, wx.ALL | wx.CENTER, 5)
        self.sizer.Add(self.remember_me_checkbox, 0, wx.ALL | wx.CENTER, 5)
        self.sizer.Add(self.login_button, 0, wx.ALL | wx.CENTER, 5)
        self.sizer.Add(self.change_password_button, 0, wx.ALL | wx.CENTER, 5)

        self.panel.SetSizerAndFit(self.sizer)
        self.Centre()
        self.logged_in_username = None
        self.logged_in_role = None
        self.stored_password_hash = ""

        self.load_saved_credentials()

    def load_saved_credentials(self):
        if os.path.exists('credentials.json'):
            with open('credentials.json', 'r') as file:
                data = json.load(file)
                self.username_text.SetValue(data.get('username', ''))
                self.stored_password_hash = data.get('password', '')
                if self.stored_password_hash:
                    self.remember_me_checkbox.SetValue(True)
                    self.password_text.SetValue(self.decrypt_password(data.get('password')))

    def encrypt_password(self, password):
        return base64.b64encode(password.encode()).decode('utf-8')

    def decrypt_password(self, hashed_password):
        return base64.b64decode(hashed_password.encode()).decode('utf-8')

    def save_credentials(self, username, password):
        hashed_password = self.encrypt_password(password)
        with open('credentials.json', 'w') as file:
            json.dump({'username': username, 'password': hashed_password}, file)

    def clear_credentials(self):
        if os.path.exists('credentials.json'):
            os.remove('credentials.json')

    def on_login(self, event):
        username = self.username_text.GetValue()
        password = self.password_text.GetValue()
        try:
            # 校验用户凭证
            pamars = {'username': username, 'password': password}
            data = http_manager.get_params(f'/validate_user', params=pamars)
            valid = data.get('valid', False)
            role = data.get('role', None)

            if valid:
                if self.remember_me_checkbox.GetValue():
                    self.save_credentials(username, password)
                else:
                    self.clear_credentials()

                self.logged_in_username = username  # 记录登录后的用户名
                self.logged_in_role = role  # 记录登录后的用户角色
                self.EndModal(wx.ID_OK)
            else:
                wx.MessageBox("Invalid username or password", "Error", wx.OK | wx.ICON_ERROR)
        except Exception as e:
            wx.MessageBox(f'未知错误: {str(e)}', 'Error', wx.OK | wx.ICON_ERROR)

    def on_change_password(self, event):
        dialog = ChangePasswordDialog(self)
        dialog.ShowModal()
        dialog.Destroy()


class ChangePasswordDialog(wx.Dialog):
    def __init__(self, parent):
        super(ChangePasswordDialog, self).__init__(parent, title="Change Password", size=(1000, 700))
        self.panel = wx.Panel(self)
        self.sizer = wx.BoxSizer(wx.VERTICAL)

        self.username_label = wx.StaticText(self.panel, label="Username:")
        self.username_text = wx.TextCtrl(self.panel, size=(200, -1))

        self.old_password_label = wx.StaticText(self.panel, label="Old Password:")
        self.old_password_text = wx.TextCtrl(self.panel, style=wx.TE_PASSWORD, size=(200, -1))

        self.new_password_label = wx.StaticText(self.panel, label="New Password:")
        self.new_password_text = wx.TextCtrl(self.panel, style=wx.TE_PASSWORD, size=(200, -1))

        self.confirm_password_label = wx.StaticText(self.panel, label="Confirm New Password:")
        self.confirm_password_text = wx.TextCtrl(self.panel, style=wx.TE_PASSWORD, size=(200, -1))

        self.change_password_button = wx.Button(self.panel, label="Change Password")
        self.change_password_button.Bind(wx.EVT_BUTTON, self.on_change_password)

        self.sizer.Add(self.username_label, 0, wx.ALL | wx.CENTER, 5)
        self.sizer.Add(self.username_text, 0, wx.ALL | wx.CENTER, 5)
        self.sizer.Add(self.old_password_label, 0, wx.ALL | wx.CENTER, 5)
        self.sizer.Add(self.old_password_text, 0, wx.ALL | wx.CENTER, 5)
        self.sizer.Add(self.new_password_label, 0, wx.ALL | wx.CENTER, 5)
        self.sizer.Add(self.new_password_text, 0, wx.ALL | wx.CENTER, 5)
        self.sizer.Add(self.confirm_password_label, 0, wx.ALL | wx.CENTER, 5)
        self.sizer.Add(self.confirm_password_text, 0, wx.ALL | wx.CENTER, 5)
        self.sizer.Add(self.change_password_button, 0, wx.ALL | wx.CENTER, 5)

        self.panel.SetSizerAndFit(self.sizer)
        self.Centre()

    def on_change_password(self, event):
        username = self.username_text.GetValue()
        old_password = self.old_password_text.GetValue()
        new_password = self.new_password_text.GetValue()
        confirm_password = self.confirm_password_text.GetValue()

        if new_password != confirm_password:
            wx.MessageBox("New passwords do not match", "Error", wx.OK | wx.ICON_ERROR)
            return
        json_data = {
            'username': username,
            'old_password': old_password,
            'new_password': new_password
        }
        try:
            data = http_manager.post_data(f'/change_user_password', json_data)
            logger.warning(data.get('result'))
            if data.get('result'):
                wx.MessageBox("Password changed successfully", "Success", wx.OK | wx.ICON_INFORMATION)
                self.EndModal(wx.ID_OK)
            else:
                wx.MessageBox("Invalid username or old password", "Error", wx.OK | wx.ICON_ERROR)
        except Exception as e:
            wx.MessageBox(f'未知错误: {str(e)}', 'Error', wx.OK | wx.ICON_ERROR)


class MainApp(wx.App):
    def OnInit(self):
        login_dialog = LoginDialog(None, title="PATVS-测试管理系统")
        if login_dialog.ShowModal() == wx.ID_OK:
            username = login_dialog.logged_in_username
            role = login_dialog.logged_in_role  # 获取用户角色

            if role == 'admin':
                frame = AdminWindow(None, title="PATVS-Admin")
            else:
                frame = MainWindow(None, title="PATVS-1.0.0.8", username=username)

            self.SetTopWindow(frame)
            frame.Show(True)
            return True
        else:
            return False

    def OnExit(self):
        # Clean up any resources before the application exits
        return 0


class MainWindow(wx.Frame):
    def __init__(self, parent, title, username):
        super(MainWindow, self).__init__(parent, title=title, size=(1000, 700))

        # tester 的界面逻辑
        self.panel = TestCasesPanel(self, username)

        # 设置图标
        if getattr(sys, 'frozen', False):
            APP_ICON = resource_path('icon/PATS.ico')
        else:
            APP_ICON = resource_path('ui_manager/icon/PATS.ico')
        icon = wx.Icon(APP_ICON, wx.BITMAP_TYPE_ICO)
        self.SetIcon(icon)

        self.Bind(wx.EVT_CLOSE, self.on_close)
        self.Centre()

    def on_close(self, event):
        self.panel.save_state()  # 调用 TestCasesPanel 类的保存状态方法
        self.Destroy()
        wx.GetApp().ExitMainLoop()  # 确保关闭事件结束主循环


class AdminWindow(wx.Frame):
    def __init__(self, parent, title):
        super(AdminWindow, self).__init__(parent, title=title, size=(1000, 700))

        # Admin用户的界面逻辑
        self.panel = TestAdminPanel(self)

        # 设置图标
        if getattr(sys, 'frozen', False):
            APP_ICON = resource_path('icon/PATS.ico')
        else:
            APP_ICON = resource_path('ui_manager/icon/PATS.ico')
        icon = wx.Icon(APP_ICON, wx.BITMAP_TYPE_ICO)
        self.SetIcon(icon)

        self.Bind(wx.EVT_CLOSE, self.on_close)
        self.Centre()

    def on_close(self, event):
        self.Destroy()
        wx.GetApp().ExitMainLoop()  # 确保关闭事件结束主循环


if __name__ == "__main__":
    app = MainApp(redirect=False)
    app.MainLoop()

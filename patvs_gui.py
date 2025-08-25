# -*- coding: utf-8 -*-
# 负责主界面展示
import wx
import winreg as reg
from ui_manager.patvs_ui_manager import TestCasesPanel
from ui_manager.patvs_admin_ui_manager import TestAdminPanel
from common.logs import logger
import sys
import os
from requests_manager.http_requests_manager import http_manager
import json
import base64
import requests


directory = "C:\\PATVS"
VERSION = "1.0.4"
if not os.path.exists(directory):
    os.makedirs(directory)
file_dir = os.path.join(directory, 'credentials.json')


def get_latest_version_info():
    resp = http_manager.get_params('/app/update')
    return resp


def get_filename_from_url(url):
    return url.split('/')[-1]


def download_file(url, save_path, on_progress=None):
    try:
        with requests.get(url, stream=True, timeout=60, verify=False) as resp:
            resp.raise_for_status()
            total = int(resp.headers.get('content-length', 0))
            downloaded = 0
            with open(save_path, 'wb') as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if on_progress and total:
                            percent = int(downloaded * 100 / total)
                            wx.CallAfter(on_progress, percent)
        return True
    except Exception as e:
        logger.error(f"下载失败: {e}")
        return False


def compare_version(v1, v2):
    def parse(v): return [int(x) for x in v.split('.')]

    return parse(v2) > parse(v1)


def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)


def is_in_startup(app_name):
    """
    检测程序是否已在开机自启动中
    :param app_name: 程序名称（注册表中的键名）
    :return: True 如果已设置为开机启动，否则 False
    """
    try:
        key = r"Software\Microsoft\Windows\CurrentVersion\Run"
        reg_key = reg.OpenKey(reg.HKEY_CURRENT_USER, key, 0, reg.KEY_READ)
        # 尝试获取注册表中的值
        value, _ = reg.QueryValueEx(reg_key, app_name)
        reg.CloseKey(reg_key)
        # 检查路径是否一致
        if value == os.path.abspath(sys.argv[0]):
            return True
    except FileNotFoundError:
        # 如果找不到键值，说明未设置
        return False
    return False


def add_to_startup(app_name):
    """
    将程序添加到开机自启动
    :param app_name: 程序名称（注册表中的键名）
    """
    try:
        exe_path = os.path.abspath(sys.argv[0])  # 当前程序路径
        key = r"Software\Microsoft\Windows\CurrentVersion\Run"
        reg_key = reg.OpenKey(reg.HKEY_CURRENT_USER, key, 0, reg.KEY_SET_VALUE)
        # 写入注册表
        reg.SetValueEx(reg_key, app_name, 0, reg.REG_SZ, exe_path)
        reg.CloseKey(reg_key)
        logger.info(f"[成功] 已将程序 '{app_name}' 添加到开机自启动")
    except Exception as e:
        logger.error(f"[失败] 无法添加到开机自启动: {e}")


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
        self.token = None
        self.logged_in_username = None
        self.logged_in_role = None
        self.stored_password_hash = ""

        self.load_saved_credentials()

    def load_saved_credentials(self):

        if os.path.exists(file_dir):
            with open(file_dir, 'r') as file:
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
        with open(file_dir, 'w') as file:
            json.dump({'username': username, 'password': hashed_password}, file)

    def clear_credentials(self):
        if os.path.exists(file_dir):
            os.remove(file_dir)

    def on_login(self, event):
        username = self.username_text.GetValue()
        password = self.password_text.GetValue()
        try:
            # 校验用户凭证
            pamars = {'username': username, 'password': password}
            data = http_manager.post_data(f'/login', data=pamars)
            role = data.get('role', None)

            if 'token' in data:
                self.token = data['token']
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
        # 检查是否已设置为开机启动
        app_name = f"Test_Tracking_System-{VERSION}"
        if not is_in_startup(app_name):
            logger.info("检测到程序未设置为开机启动，正在添加...")
            add_to_startup(app_name)
            wx.MessageBox("程序已成功设置为开机自启动", "提示", wx.OK | wx.ICON_INFORMATION)

        # 创建一个隐藏的Frame，防止主循环提前退出
        self.dummy_frame = wx.Frame(None)
        self.dummy_frame.Hide()

        # 启动线程检查更新
        import threading
        threading.Thread(target=self.check_update_thread, daemon=True).start()
        return True  # 先让主循环跑起来

    def check_update_thread(self):
        try:
            info = get_latest_version_info()
            if not info:
                wx.CallAfter(self.show_login_dialog)
                return

            latest_ver = info['version']
            desc = info.get('desc', '')
            url = info['url']

            if compare_version(VERSION, latest_ver):
                # 弹窗必须在主线程
                def ask_update():
                    dlg = wx.MessageDialog(None,
                                           f"检测到新版本 {latest_ver}：\n{desc}\n\n是否下载并安装？",
                                           "发现新版本", wx.YES_NO | wx.ICON_INFORMATION)
                    if dlg.ShowModal() == wx.ID_YES:
                        dlg.Destroy()
                        self.download_update_thread(url)
                    else:
                        dlg.Destroy()
                        self.show_login_dialog()

                wx.CallAfter(ask_update)
            else:
                wx.CallAfter(self.show_login_dialog)
        except Exception as e:
            logger.error(f"检测更新异常: {e}")
            wx.CallAfter(self.show_login_dialog)

    def download_update_thread(self, url):
        filename = get_filename_from_url(url)

        # 获取当前用户的桌面路径
        desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
        save_path = os.path.join(desktop_path, filename)

        # 进度条必须在主线程创建
        wx.CallAfter(self.start_download_progress, url, save_path)

    def start_download_progress(self, url, save_path):
        progress_dlg = wx.ProgressDialog("下载更新至-C://PATVS", "正在下载新版本...", maximum=100, parent=None)
        import threading

        def on_progress(percent):
            progress_dlg.Update(percent)

        def do_download():
            ok = download_file(url, save_path, on_progress)
            wx.CallAfter(progress_dlg.Destroy)
            if ok:
                wx.CallAfter(self.download_success, save_path)
            else:
                wx.CallAfter(self.download_failed)

        threading.Thread(target=do_download, daemon=True).start()

    def download_success(self, save_path):
        wx.MessageBox("下载成功，即将安装新版本", "提示", wx.OK | wx.ICON_INFORMATION)
        os.startfile(save_path)
        wx.GetApp().ExitMainLoop()
        sys.exit(0)

    def download_failed(self):
        wx.MessageBox("下载失败，请稍后重试", "错误", wx.OK | wx.ICON_ERROR)
        self.show_login_dialog()

    def show_login_dialog(self):
        login_dialog = LoginDialog(None, title=f"TTS-测试管理系统-{VERSION}")
        if login_dialog.ShowModal() == wx.ID_OK:
            username = login_dialog.logged_in_username
            token = login_dialog.token
            role = login_dialog.logged_in_role

            if role == 'admin':
                frame = AdminWindow(None, title=f"Test Tracking System-Admin-{VERSION}", username=username, token=token)
            else:
                frame = MainWindow(None, title=f"Test Tracking System-{VERSION}", username=username, token=token)

            self.SetTopWindow(frame)
            frame.Show(True)
        else:
            wx.GetApp().ExitMainLoop()

    def OnExit(self):
        # Clean up any resources before the application exits
        return 0


class MainWindow(wx.Frame):
    def __init__(self, parent, title, username, token):
        super(MainWindow, self).__init__(parent, title=title, size=(1000, 700))

        # tester 的界面逻辑
        self.panel = TestCasesPanel(self, username, token)

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
    def __init__(self, parent, title, username, token):
        super(AdminWindow, self).__init__(parent, title=title, size=(1000, 700))

        # Admin用户的界面逻辑
        self.panel = TestAdminPanel(self, username, token)

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

# -*- coding: utf-8 -*-
# 负责GUI界面展示以及交互逻辑
import os
import json

import pywintypes
import requests
import win32process
import wx
import wx.grid
import subprocess
import threading
import openpyxl
import sys
from functools import partial
from monitor_manager.patvs_fuction import Patvs_Fuction
from openpyxl.styles import PatternFill
from openpyxl.styles import Font
from monitor_manager.up_files import run_main
from monitor_manager.devicerm import Notification
from common.rw_excel import MyExcel
from datetime import datetime
from common.logs import logger
import win32con
import win32api
from requests_manager.http_requests_manager import http_manager
import win32gui


def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)


class ResetButtonRenderer(wx.grid.GridCellRenderer):
    def __init__(self):
        wx.grid.GridCellRenderer.__init__(self)

    def Draw(self, grid, attr, dc, rect, row, col, isSelected):
        button_text = "重置"
        dc.SetBrush(wx.Brush("white"))
        dc.SetPen(wx.TRANSPARENT_PEN)
        dc.DrawRectangle(rect)
        tw, th = dc.GetTextExtent(button_text)
        # 保持水平垂直居中
        dc.SetTextForeground(wx.BLUE)
        dc.DrawText(button_text, rect.x + rect.width // 2 - tw // 2, rect.y + rect.height // 2 - th // 2)


class TestCasesPanel(wx.Panel):
    def __init__(self, parent, username):
        super().__init__(parent)
        # 在主线程中创建一个事件,用来通知阻塞情况下终止线程
        self.stop_event = True
        self.patvs_monitor = Patvs_Fuction(self, self.stop_event)
        self.username = username  # 保存用户名
        self.splitter = wx.SplitterWindow(self)
        # 初始化 log_splitter
        self.log_splitter = wx.SplitterWindow(self.splitter)
        self.tree = wx.TreeCtrl(self.splitter, style=wx.TR_DEFAULT_STYLE)
        self.content = wx.TextCtrl(self.log_splitter, style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_RICH2)
        self.log_content = wx.TextCtrl(self.log_splitter, style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_RICH2)

        # 初始化分隔条，确保位置设置稳定
        self.log_splitter.SetMinimumPaneSize(20)  # 设置最小窗格尺寸
        self.log_splitter.SplitHorizontally(self.content, self.log_content, sashPosition=-200)
        self.log_splitter.SetSashGravity(0.8)

        self.splitter.SetMinimumPaneSize(20)
        self.splitter.SplitVertically(self.tree, self.log_splitter, sashPosition=200)
        self.splitter.SetSashGravity(0.2)

        # 上传按钮
        upload_icon = wx.Bitmap(resource_path("icon\\上传文件夹.png"))
        self.upload_button = wx.BitmapButton(self, bitmap=upload_icon)
        self.upload_button.SetToolTip(wx.ToolTip("上传文件"))
        self.upload_button.Bind(wx.EVT_BUTTON, self.up_file)

        # 检查按钮
        device_icon = wx.Bitmap(resource_path("icon\\设备管理.png"))
        # self.check_button = wx.Button(self, label='检查')
        self.device_button = wx.BitmapButton(self, bitmap=device_icon)
        self.device_button.SetToolTip(wx.ToolTip("打开设备管理器"))
        self.device_button.Bind(wx.EVT_BUTTON, self.open_device_manager)

        # 配置按钮
        config_icon = wx.Bitmap(resource_path("icon\\configure.png"))
        self.config_button = wx.BitmapButton(self, bitmap=config_icon)
        self.config_button.SetToolTip(wx.ToolTip("生成配置文件"))
        self.config_button.Bind(wx.EVT_BUTTON, self.write_config)

        # 查看用例状态按钮
        status_icon = wx.Bitmap(resource_path("icon\\查看状态1.png"))
        self.status_button = wx.BitmapButton(self, bitmap=status_icon)
        self.status_button.SetToolTip(wx.ToolTip("查看用例状态"))
        self.status_button.Bind(wx.EVT_BUTTON, self.check_status)

        # 附件按钮
        annex_icon = wx.Bitmap(resource_path("icon\\附件.png"))
        self.annex_button = wx.BitmapButton(self, bitmap=annex_icon)
        self.annex_button.SetToolTip(wx.ToolTip("上传附件"))
        self.annex_button.Bind(wx.EVT_BUTTON, self.select_annex)

        # 用例筛选下拉框
        self.plan_name_combo = wx.ComboBox(self, choices=http_manager.get_plan_names(self.username))
        self.plan_name_combo.Bind(wx.EVT_COMBOBOX, self.on_plan_select)

        # 添加新的下拉框用于显示 sheet_name
        self.sheet_name_combo = wx.ComboBox(self)
        self.sheet_name_combo.Bind(wx.EVT_COMBOBOX, self.on_sheet_select)

        # 图片
        lenovo_bitmap = wx.Bitmap(resource_path("icon\\3332.png"), wx.BITMAP_TYPE_ANY)
        imageCtrl = wx.StaticBitmap(self, bitmap=lenovo_bitmap)

        # 下拉框 监控动作、测试次数
        # self.monitor_actions = ['时间', '电源插拔', 'S3+电源插拔', 'S3', 'S4', 'S5', 'Restart',
        #                         '键盘按键', 'USB插拔', 'S3+USB插拔', '锁屏', '鼠标点击']
        self.monitor_actions = ['时间', '电源插拔', 'S3+电源插拔', 'S3', 'S4', 'S5', 'Restart',
                                '键盘按键', 'USB插拔', '锁屏', '鼠标点击']
        self.tests_num = ['1', '3', '5', '10', '20', '50', '100', '300', '500', '1000']
        self.actions_box = wx.ComboBox(self, choices=self.monitor_actions)
        self.tests_box = wx.ComboBox(self, choices=self.tests_num)

        # start、pass、fail、block 按钮
        self.start_button = wx.Button(self, label='start')
        self.start_button.Bind(wx.EVT_BUTTON, self.start_test)

        # 创建一个字体对象，字体大小为16，字体家族为瑞士，风格为正常，但是字体粗细为加粗
        font = wx.Font(12, wx.SWISS, wx.NORMAL, wx.NORMAL)

        # 创建布局，将按钮放置在左上角
        buttonSizer = wx.BoxSizer(wx.HORIZONTAL)

        # 将按钮添加到布局中
        buttonSizer.Add(self.upload_button, 0, wx.ALL, 5)
        buttonSizer.Add(self.device_button, 0, wx.ALL, 5)
        buttonSizer.Add(self.config_button, 0, wx.ALL, 5)
        buttonSizer.Add(self.status_button, 0, wx.ALL, 5)
        buttonSizer.Add(self.annex_button, 0, wx.ALL, 5)
        # 添加弹性空间，负责将后续的控件推向中间
        buttonSizer.AddStretchSpacer(prop=1)

        # 添加居中的标签（初始为空）
        self.case_time_total = wx.StaticText(self, label="总耗时: N/A")
        self.case_time_total.SetFont(font)
        buttonSizer.Add(self.case_time_total, 0, wx.ALIGN_CENTER | wx.ALL, 5)

        # 添加间隙,以像素为单位的间隔宽度
        buttonSizer.AddSpacer(30)
        self.case_total = wx.StaticText(self, label="用例总数: N/A")
        self.case_total.SetFont(font)
        buttonSizer.Add(self.case_total, 0, wx.ALIGN_CENTER | wx.ALL, 5)

        # 添加间隙,以像素为单位的间隔宽度
        buttonSizer.AddSpacer(100)

        self.executed_cases = wx.StaticText(self, label="已执行用例: N/A")
        self.executed_cases.SetFont(font)  # 设置字体大小
        buttonSizer.Add(self.executed_cases, 0, wx.ALIGN_CENTER | wx.ALL, 5)

        # 再次添加弹性空间，确保标签之后的空间与之前的空间保持平衡
        buttonSizer.AddStretchSpacer(prop=1)

        # 创建主布局
        mainSizer = wx.BoxSizer(wx.VERTICAL)

        # 在主布局中加入按钮布局，并使其水平居中
        mainSizer.Add(buttonSizer, 0, wx.EXPAND)

        # 单独创建一个水平盒子来放置 case_search_combo 下拉框
        caseSearchSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.testerLabel = wx.StaticText(self, label=f"测试人员: {username}")
        #    self.testerLabel.SetFont(font)
        caseSearchSizer.Add(self.testerLabel, 0, wx.ALL, 5)

        self.planLabel = wx.StaticText(self, label="测试计划")
        caseSearchSizer.Add(self.planLabel, 0, wx.ALL, 5)
        caseSearchSizer.Add(self.plan_name_combo, 0, wx.ALL, 5)

        self.sheetLabel = wx.StaticText(self, label="测试用例")
        caseSearchSizer.Add(self.sheetLabel, 0, wx.ALL, 5)
        caseSearchSizer.Add(self.sheet_name_combo, 0, wx.ALL, 5)

        # 添加透明占位符,保持对齐
        dummyLabel = wx.StaticText(self, label="")
        dummyLabel.SetMinSize((60, -1))
        caseSearchSizer.Add(dummyLabel, 0, wx.EXPAND)

        #  caseSearchSizer.AddStretchSpacer(prop=1)
        caseSearchSizer.AddSpacer(10)
        self.test_progress = wx.StaticText(self, label="测试进度: N/A")
        self.test_progress.SetFont(font)  # 设置字体大小
        caseSearchSizer.Add(self.test_progress, 0, wx.ALIGN_CENTER | wx.ALL, 5)
        caseSearchSizer.AddSpacer(10)
        self.passing_rate = wx.StaticText(self, label="通过率: N/A")
        self.passing_rate.SetFont(font)  # 设置字体大小
        caseSearchSizer.Add(self.passing_rate, 0, wx.ALIGN_CENTER | wx.ALL, 5)
        caseSearchSizer.AddStretchSpacer(prop=1)

        # 在主布局中加入 case_search_combo 布局，确保它在按钮下方
        mainSizer.Add(caseSearchSizer, 0, wx.EXPAND)

        # 创建新的布局，将下拉框和按钮放在右下脚
        actionSizer = wx.BoxSizer(wx.HORIZONTAL)
        buttonSizer2 = wx.BoxSizer(wx.HORIZONTAL)
        # 创建按钮并添加到布局
        self.result_buttons = {}
        for button in ['Pass', 'Fail', 'Block']:
            self.result_buttons[button] = wx.Button(self, label=button)
            self.result_buttons[button].Bind(wx.EVT_BUTTON, self.test_result)
            buttonSizer2.Add(self.result_buttons[button], 0, wx.ALL, 5)
            self.result_buttons[button].Hide()

        # 添加下拉框到新的布局
        actionSizer.Add(wx.StaticText(self, label="监控动作:"), 0, wx.ALL, 5)
        actionSizer.Add(self.actions_box, 0, wx.ALL, 5)
        actionSizer.Add(wx.StaticText(self, label="测试次数:"), 0, wx.ALL, 5)
        actionSizer.Add(self.tests_box, 0, wx.ALL, 5)

        # 添加按钮到新的布局
        buttonSizer2.Add(self.start_button, 0, wx.ALL, 5)

        # 在主布局中添加按钮布局和新的布局
        mainSizer.Add(self.splitter, 1, wx.EXPAND)

        # 创建底部布局，将下拉框和按钮放在右侧
        bottomSizer = wx.BoxSizer(wx.HORIZONTAL)
        # 添加图片到布局（最左边）
        bottomSizer.Add(imageCtrl, 0, wx.ALL | wx.ALIGN_LEFT, 5)
        bottomSizer.Add(actionSizer, 0, wx.ALL, 5)
        bottomSizer.Add(buttonSizer2, 0, wx.ALL, 5)
        mainSizer.Add(bottomSizer, 0, wx.ALL, 5)

        # 设置主布局
        self.SetSizer(mainSizer)
        # 初始时不显示用例树，等待用户选择计划和用例表后显示
        self.tree.Hide()
        # 初始时没有用例树数据
        self.testCases = None
        self.sheet_id = None
        self.CaseID = None
        self.tree.Bind(wx.EVT_TREE_SEL_CHANGED, self.OnSelChanged)
        # 如果有记录，显示上一次打开的页面
        self.restore_state()

    def on_plan_select(self, event):
        # 选择测试计划后，更新用例表下拉框
        logger.warning('开始调用 plan select')
        plan_name = self.plan_name_combo.GetValue()
        sheet_names_with_ids = http_manager.get_sheet_names(plan_name, self.username)

        # 清空并重新填充 sheet_name_combo
        self.sheet_name_combo.Clear()
        for sheet_id, sheet_name in sheet_names_with_ids:
            self.sheet_name_combo.Append(sheet_name, sheet_id)
        self.tree.Hide()  # 选择计划后先隐藏用例树，等待选择用例表后再显示
        # 清空统计信息
        self.clear_statistics()
        logger.warning('调用 plan select 结束')

    def on_sheet_select(self, event):
        # 选择用例表后，更新用例树
        selected_index = self.sheet_name_combo.GetSelection()
        if selected_index != wx.NOT_FOUND:
            self.sheet_id = self.sheet_name_combo.GetClientData(selected_index)
            self.sheet_name = self.sheet_name_combo.GetString(selected_index)
            self.testCases = self.PopulateTree(self.sheet_id, self.sheet_name)  # 使用 sheet_id 获取用例树
            self.tree.Show()  # 选择用例表后显示用例树
            # 更新统计信息
            self.update_statistics()

    def clear_statistics(self):
        # 清空统计信息
        self.case_time_total.SetLabel("总耗时: N/A")
        self.case_total.SetLabel("用例总数: N/A")
        self.executed_cases.SetLabel("已执行用例: N/A")
        self.test_progress.SetLabel("测试进度: N/A")
        self.passing_rate.SetLabel("通过率: N/A")

    def update_statistics(self):
        # 更新统计信息
        if self.sheet_id:
            data = http_manager.get_params(f'/calculate_progress_and_pass_rate/{self.sheet_id}')
            result = data.get('result')
            self.case_time_total.SetLabel(f"总耗时: {result['case_time_count']}(Min)")
            self.case_total.SetLabel(f"用例总数: {result['case_count']}")
            self.executed_cases.SetLabel(f"已执行用例: {result['executed_cases_count']}")
            self.test_progress.SetLabel(f"测试进度: {result['execution_progress']}")
            self.passing_rate.SetLabel(f"通过率: {result['pass_rate']}")

    def show_message_box(self, message, total):
        dlg = wx.MessageDialog(self, message, "测试进度", wx.YES_NO | wx.ICON_QUESTION)
        result = dlg.ShowModal()
        dlg.Destroy()

        if result == wx.ID_YES:
            self.timer = wx.Timer(self)
            self.Bind(wx.EVT_TIMER, self.on_timer)
            self.timer.Start(500)  # 3秒后触发定时器事件
        else:
            wx.CallAfter(self.add_log_message, "测试终止，请填写 block 原因。")

    def on_timer(self, event):
        self.timer.Stop()
        self.GetParent().Close()

    def save_state(self):
        state = {
            'username': self.username,
            'test_plan': self.plan_name_combo.GetValue() if self.plan_name_combo.GetValue() else None,
            'test_sheet': self.sheet_name_combo.GetValue() if self.sheet_name_combo.GetValue() else None,
            'sheet_id': self.sheet_id,
            'test_case_id': self.tree.GetItemData(
                self.tree.GetSelection()) if self.tree.GetSelection().IsOk() else None,
            'test_actions': self.actions_box.GetValue() if self.actions_box.GetValue() else None,
            'tests_box': self.tests_box.GetValue() if self.tests_box.GetValue() else None,
            'start_clicked': self.start_clicked if hasattr(self, 'start_clicked') else False
        }
        logger.info('Saving state.')
        with open('window_state.json', 'w') as state_file:
            json.dump(state, state_file)

    def restore_state(self):
        try:
            with open('window_state.json', 'r') as state_file:
                state = json.load(state_file)
                # 防止 username 篡改数据
                if state['username'] == self.username:
                    if 'test_plan' in state and state['test_plan']:
                        self.plan_name_combo.SetValue(state['test_plan'])
                        self.on_plan_select(None)
                    if 'test_sheet' in state and state['test_sheet']:
                        sheet_name = state['test_sheet']
                        sheet_id = state.get('sheet_id', None)
                        sheet_names_with_ids = http_manager.get_sheet_names(state['test_plan'], self.username)

                        # 清空并重新填充 sheet_name_combo
                        self.sheet_name_combo.Clear()
                        for sid, sname in sheet_names_with_ids:
                            self.sheet_name_combo.Append(sname, sid)
                            # 如果找到匹配的 sheet_name，设置选项和客户端数据
                            if sname == sheet_name and sid == sheet_id:
                                selected_index = self.sheet_name_combo.FindString(sheet_name)
                                if selected_index != wx.NOT_FOUND:
                                    self.sheet_name_combo.SetSelection(selected_index)
                                    self.sheet_name_combo.SetClientData(selected_index, sheet_id)
                                    logger.info(f"Restored sheet_name: {sheet_name}, sheet_id: {sheet_id}")
                                    self.on_sheet_select(None)  # 在找到匹配的sheet_name和sheet_id时调用
                    if 'test_case_id' in state and state['test_case_id']:
                        self.set_tree_selection_by_id(state['test_case_id'])
                    if 'test_actions' in state and state['test_actions']:
                        self.actions_box.SetValue(state['test_actions'])
                    if 'tests_box' in state and state['tests_box']:
                        self.tests_box.SetValue(state['tests_box'])
                    if 'start_clicked' in state and state['start_clicked']:
                        self.start_clicked = True
                        self.start_test(None)
                    else:
                        self.start_clicked = False
        except FileNotFoundError:
            logger.info('State file not found, starting with default state.')
            self.Center()

    def set_tree_selection_by_id(self, case_id):
        root = self.tree.GetRootItem()
        if root:
            self.expand_and_select_by_id(root, case_id, [])

    def expand_and_select_by_id(self, item, case_id, path):
        if self.tree.GetItemData(item) == case_id:
            for p_item in path:
                self.tree.Expand(p_item)
            self.tree.SelectItem(item)
            wx.CallAfter(self.tree.EnsureVisible, item)  # Make sure the item is visible
            wx.CallAfter(self.tree.SetFocus)  # Set focus to the tree
            return True

        path.append(item)
        child, cookie = self.tree.GetFirstChild(item)
        while child.IsOk():
            if self.expand_and_select_by_id(child, case_id, path):
                return True
            child, cookie = self.tree.GetNextChild(item, cookie)
        path.pop()
        return False

    def add_log_message(self, message):
        """向日志窗口添加消息"""
        if self.log_content:
            self.log_content.AppendText(message + '\n')  # 在文本控件的末尾添加文本

    def test_result(self, event):

        clicked_button = event.GetEventObject()
        case_result = clicked_button.GetLabel()
        if clicked_button is self.result_buttons['Pass']:
            # 处理 pass
            logger.info(f"Pass Button clicked {self.CaseID}")
            http_manager.update_end_time_case_id(self.CaseID, 'Pass')
            wx.CallAfter(self.case_enable)
            wx.CallAfter(self.refresh_node_case_status, case_status=case_result)
            wx.CallAfter(self.update_statistics)
        elif clicked_button in [self.result_buttons['Fail'], self.result_buttons['Block']]:
            # 处理 fail or block
            # 弹出文本输入对话框
            dlg = wx.TextEntryDialog(self, '请输入Fail/Block原因 :', 'Comment')
            if dlg.ShowModal() == wx.ID_OK:
                input_content = dlg.GetValue().strip()  # 获取输入的内容
                if input_content:
                    logger.info(f"{case_result} Button clicked, Content: {input_content}")
                    http_manager.update_end_time_case_id(self.CaseID, case_result, input_content)
                    wx.CallAfter(self.case_enable)
                    wx.CallAfter(self.refresh_node_case_status, case_status=case_result)
                    wx.CallAfter(self.update_statistics)
                    # 设置事件以通知监控线程停止
                    self.patvs_monitor.stop_event = False
                    # 当用例为 block 时，需要主动去停止 messageLoop 的循环
                    try:
                        win32api.PostThreadMessage(self.msg_loop_thread_id, win32con.WM_QUIT, 0, 0)
                    except pywintypes.error as e:
                        logger.warning(f"{e}")
                    except:
                        pass
                else:
                    wx.MessageDialog(self, '内容不能为空，请重新输入!', '错误', style=wx.OK | wx.ICON_ERROR).ShowModal()
            dlg.Destroy()
        self.start_clicked = False

    def start_test(self, event):
        self.start_clicked = True
        # 检查是否有选中的用例
        if not hasattr(self, 'CaseID') or not self.CaseID:
            wx.MessageBox('请先选择用例', 'Warning')
            return
        action = self.actions_box.GetValue()
        num_test = self.tests_box.GetValue()
        if not action or not num_test:
            wx.MessageBox('监控动作/测试次数不能为空', 'Warning')
            return
        result = http_manager.get_params(f'/get_case_result/{self.CaseID}')
        if result.get('case_result'):
            wx.MessageBox('已有测试结果，请重置此条测试用例后再进行测试', 'Warning')
            return
        wx.CallAfter(self.case_disable)
        http_manager.post_data('/update_start_time', {'case_id': self.CaseID, 'actions': action, 'actions_num': num_test})
        # 初始化终止信号
        self.patvs_monitor.stop_event = True
        # 使用多线程异步运行，防止GUI界面卡死
        if action == '时间':
            while True:
                dlg = wx.TextEntryDialog(self, '请输入需要测试的时间(in minutes):', '监控时间', '1')
                if dlg.ShowModal() == wx.ID_OK:
                    try:
                        num_time = float(dlg.GetValue())
                        if num_time > 0:
                            num_time = num_time * 60  # 转换为秒
                            break
                        else:
                            wx.MessageBox('请输入一个正数。', '输入错误', wx.OK | wx.ICON_ERROR)
                    except ValueError:
                        wx.MessageBox('请输入一个有效的正整数。', '输入错误', wx.OK | wx.ICON_ERROR)
                else:
                    wx.MessageBox('This input is required to proceed.', 'Input Required', wx.OK | wx.ICON_WARNING)
            self.add_log_message(f"您选择的动作是: {action}，目标测试次数{num_test}，目标测试时间: {num_time}S")
            thread = threading.Thread(target=self.patvs_monitor.monitor_time, args=(int(num_time), int(num_test),))
            thread.setDaemon(True)
            thread.start()
        elif action == '电源插拔':
            self.add_log_message(f"您选择的动作是: {action}，目标测试次数: {num_test}")
            thread = threading.Thread(target=self.patvs_monitor.start_monitoring_power, args=(int(num_test),))
            thread.setDaemon(True)
            thread.start()
        elif action == 'S3+电源插拔':
            self.add_log_message(f"您选择的动作是: {action}，目标测试次数: {num_test}")
            thread = threading.Thread(target=self.patvs_monitor.start_monitoring_s3_and_power, args=(int(num_test),))
            thread.setDaemon(True)
            thread.start()
        elif action == 'S3':
            self.add_log_message(f"您选择的动作是: {action}，目标测试次数: {num_test}")
            start_time = http_manager.get_start_time(self.CaseID)
            thread = threading.Thread(target=self.patvs_monitor.test_count_s3_sleep_events,
                                      args=(str(start_time), int(num_test),))
            thread.setDaemon(True)
            thread.start()
        elif action == 'S4':
            self.add_log_message(f"您选择的动作是: {action}，目标测试次数: {num_test}")
            start_time = http_manager.get_start_time(self.CaseID)
            thread = threading.Thread(target=self.patvs_monitor.test_count_s4_sleep_events,
                                      args=(str(start_time), int(num_test),))
            thread.setDaemon(True)
            thread.start()
        elif action == 'S5':
            self.add_log_message(f"您选择的动作是: {action}，目标测试次数: {num_test}")
            start_time = http_manager.get_start_time(self.CaseID)
            thread = threading.Thread(target=self.patvs_monitor.test_count_s5_sleep_events,
                                      args=(str(start_time), int(num_test),))
            thread.setDaemon(True)
            thread.start()
        elif action == 'Restart':
            self.add_log_message(f"您选择的动作是: {action}，目标测试次数: {num_test}")
            start_time = http_manager.get_start_time(self.CaseID)
            logger.warning(type(start_time))
            logger.warning(start_time)
            thread = threading.Thread(target=self.patvs_monitor.test_count_restart_events,
                                      args=(str(start_time), int(num_test),))
            thread.setDaemon(True)
            thread.start()
        elif action == 'USB插拔':
            self.add_log_message(f"您选择的动作是: {action}，目标测试次数: {num_test}")
            msg_loop_thread = threading.Thread(target=self.patvs_monitor.monitor_device_plug_changes,
                                               args=(int(num_test),))
            msg_loop_thread.setDaemon(True)
            msg_loop_thread.start()
            # 获取线程ID
            self.msg_loop_thread_id = msg_loop_thread.ident

        # elif action == 'S3+USB插拔':
        #     self.add_log_message(f"您选择的动作是: {action}，目标测试次数: {num_test}")
        #     msg_loop_thread = threading.Thread(target=self.patvs_monitor.s3_and_device_plug_changes,
        #                                        args=(int(num_test),))
        #     msg_loop_thread.setDaemon(True)
        #     msg_loop_thread.start()
        #     # 获取线程ID
        #     self.msg_loop_thread_id = msg_loop_thread.ident
        elif action == '键盘按键':
            self.add_log_message(f"您选择的动作是: {action}，目标测试次数: {num_test}")
            msg_loop_thread = threading.Thread(target=self.patvs_monitor.monitor_keystrokes,
                                               args=(int(num_test),))
            msg_loop_thread.setDaemon(True)
            msg_loop_thread.start()
            # 获取线程ID
            self.msg_loop_thread_id = msg_loop_thread.ident
        elif action == '锁屏':
            self.add_log_message(f"您选择的动作是: {action}，目标测试次数: {num_test}")
            msg_loop_thread = threading.Thread(target=self.patvs_monitor.monitor_lock_screen_changes,
                                               args=(int(num_test),))
            msg_loop_thread.setDaemon(True)
            msg_loop_thread.start()
            # 获取线程ID
            self.msg_loop_thread_id = msg_loop_thread.ident
        elif action == '鼠标点击':
            self.add_log_message(f"您选择的动作是: {action}，目标测试次数: {num_test}")
            msg_loop_thread = threading.Thread(target=self.patvs_monitor.monitor_mouse_clicks,
                                               args=(int(num_test),))
            msg_loop_thread.setDaemon(True)
            msg_loop_thread.start()
            # 获取线程ID
            self.msg_loop_thread_id = msg_loop_thread.ident

    def after_test(self):
        for button in self.result_buttons:
            self.result_buttons[button].Enable()
        self.Layout()

    def case_disable(self):
        """
        case 执行状态按钮显示
        :return:
        """
        self.tests_box.Disable()
        self.actions_box.Disable()
        self.plan_name_combo.Disable()
        self.sheet_name_combo.Disable()
        self.tree.Disable()
        self.start_button.Hide()
        for button in self.result_buttons:
            self.result_buttons[button].Show()
        self.result_buttons['Pass'].Disable()
        self.result_buttons['Fail'].Disable()
        self.Layout()

    def case_enable(self):
        """
        case 未执行状态按钮显示
        :return:
        """
        self.tree.Enable()
        self.actions_box.Enable()
        self.tests_box.Enable()
        self.plan_name_combo.Enable()
        self.sheet_name_combo.Enable()
        self.start_button.Show()
        for button in self.result_buttons:
            self.result_buttons[button].Hide()
        self.Layout()

    def refresh_node_case_status(self, case_id=None, case_status=None):
        root = self.tree.GetRootItem()
        if case_id is None:
            case_id = self.CaseID
        if not root.IsOk():
            return
        # 遍历所有的子节点
        (item, cookie) = self.tree.GetFirstChild(root)
        while item:
            # 如果当前节点的ID匹配，那么更新这个节点的图标
            if self.tree.GetItemData(item) == case_id:
                # 重置时 status 为 None
                if case_status is not None:
                    self.tree.SetItemImage(item, self.icon_indices[case_status])
                else:
                    self.tree.SetItemImage(item, self.icon_indices['None'])
                break
            # 获取下一个节点
            (item, cookie) = self.tree.GetNextChild(root, cookie)

    def up_file(self, event):
        # 打开文件对话框
        with wx.FileDialog(self, "选择测试用例文件", wildcard="文本文件 (*.xlsx)|*.xlsx",
                           style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as fileDialog:
            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return
            # 获取选择的文件路径
            pathname = fileDialog.GetPath()
            filename = os.path.basename(pathname)  # 获取文件名
            # 校验文件是否已存在
            result = http_manager.get_params(f'/get_filename/{filename}')
            logger.warning('file_exists:', result.get('file_exists'))
            if result.get('file_exists'):
                wx.MessageBox(f"当前文件已存在，请勿重复上传", "提示", wx.OK | wx.ICON_WARNING)
                return

            # 显示等待提示框
            wait_dialog = wx.BusyInfo("正在上传和解析文件，请稍候...", self)

            def complete_upload():
                try:
                    run_main(pathname)
                    wx.CallAfter(wx.MessageBox, "文件上传和解析成功", "提示", wx.OK | wx.ICON_INFORMATION)
                except Exception as e:
                    # 格式校验出错
                    wx.CallAfter(wx.MessageBox, f"上传的用例格式不符合规则，请按照模板导入用例。错误详情: {e}", "提示",
                                 wx.OK | wx.ICON_WARNING)
                    # 关闭等待提示框
                    wx.CallAfter(lambda: wait_dialog.__exit__(None, None, None))
                    return
                finally:
                    # 关闭等待提示框
                    wx.CallAfter(lambda: wait_dialog.__exit__(None, None, None))

                # 更新显示
                all_plans = http_manager.get_plan_names(self.username)
                self.tree.DeleteAllItems()  # 清空现有的树状结构
                self.plan_name_combo.Clear()
                self.sheet_name_combo.Clear()  # 先清除之前的选项
                self.plan_name_combo.AppendItems(all_plans)  # 添加新的选项
                # plan_name = self.sql.select_plan_name_by_filename(filename)
                # if plan_name:
                #     self.plan_name_combo.SetValue(plan_name)
                #     self.on_plan_select(None)  # 自动加载 test_sheet

                self.plan_name_combo.SetValue(all_plans[0])
                self.on_plan_select(None)  # 自动加载 test_sheet
            wx.CallAfter(complete_upload)

            # self.sheet_name_combo.SetValue(self.sheet_name)
            # self.sheet_name_combo.SetValue(self.sheet_name)
            # self.testCases = self.PopulateTree(self.sheet_name)
            # # 使用 partial可以提前填充一个参数，得到一个只需要一个参数的新函数
            # self.tree.Bind(wx.EVT_TREE_SEL_CHANGED, self.OnSelChanged)

    def open_device_manager(self, event):
        """
        打开Windows设备管理器
        :param event:
        :return:
        """

        def run_command():
            subprocess.run('mmc devmgmt.msc', shell=True)

        threading.Thread(target=run_command).start()

    def write_config(self, event):
        """
        写入配置信息/暂时不知道具体用途
        :param event:
        :return:
        """
        # 创建一个对话框用于输入配置信息
        dialog = wx.Dialog(None, title="配置信息", size=(350, 350))
        panel = wx.Panel(dialog)
        vbox = wx.BoxSizer(wx.VERTICAL)

        # 创建 BIOS,ECFW,MEFW, System SN,Retimer 的输入项
        labels = ["BIOS", "ECFW", "MEFW", "System SN", "Retimer"]
        self.inputs = {}
        for label in labels:
            hbox = wx.BoxSizer(wx.HORIZONTAL)
            st = wx.StaticText(panel, label=label)
            tc = wx.TextCtrl(panel)
            hbox.Add(st)
            hbox.Add(tc, flag=wx.LEFT, border=5)
            vbox.Add(hbox, flag=wx.EXPAND | wx.ALL, border=10)
            self.inputs[label] = tc

        # 为确认和取消按钮创建一行
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        okButton = wx.Button(panel, label='保存')
        closeButton = wx.Button(panel, label='取消')

        # 绑定按钮事件
        okButton.Bind(wx.EVT_BUTTON, partial(self.save_config, dialog=dialog))
        closeButton.Bind(wx.EVT_BUTTON, partial(self.close_dialog, dialog=dialog))

        hbox.Add(okButton)
        hbox.Add(closeButton, flag=wx.LEFT, border=5)
        vbox.Add(hbox, flag=wx.ALIGN_CENTER | wx.TOP | wx.BOTTOM, border=10)

        panel.SetSizer(vbox)
        dialog.ShowModal()
        dialog.Destroy()

    def save_config(self, event, dialog):
        with open('config.txt', 'w') as f:
            for label, tc in self.inputs.items():
                f.write(f"{label}: {tc.GetValue()}\n")
        dialog.Close()
        wx.MessageBox("配置文件保存成功！", "信息", wx.OK | wx.ICON_INFORMATION)

    def close_dialog(self, event, dialog):
        dialog.Close()

    def check_status(self, event):
        # 创建一个新的对话框，并且允许对话框最大化
        dialog = wx.Dialog(self, title="查看用例状态", size=(800, 600), style=wx.MAXIMIZE_BOX | wx.DEFAULT_DIALOG_STYLE)

        # 创建grid并设置行和列
        self.grid = wx.grid.Grid(dialog)
        all_case = http_manager.get_cases_by_sheet_id(self.sheet_id)
        self.grid.CreateGrid(numRows=len(all_case), numCols=len(all_case[0]) - 2)

        # 设置列标题
        cols_title = ['测试结果', '测试耗时(S)', '选择次数', '测试机型', '用例标题', '前置条件', '用例步骤', '预期结果',
                      '开始时间', '完成时间', '测试动作', '评论']
        for i, title in enumerate(cols_title):
            self.grid.SetColLabelValue(i, title)

        # 填充数据
        self.case_row_to_id = {}
        for i, case in enumerate(all_case):
            self.case_row_to_id[i] = case[-2]  # 赋值ID为重置按钮使用
            for j, item in enumerate(case[:-2]):  # 排除ID等敏感数据

                self.grid.SetCellValue(i, j, str(item))  # 第i行，第j列，数据
                # 检查测试结果列，设置背景颜色
                if cols_title[j] == '测试结果':
                    if item == 'Pass':
                        self.grid.SetCellBackgroundColour(i, j, wx.Colour(144, 238, 144))  # 浅绿色
                    elif item == 'Fail' or item == 'Block':
                        self.grid.SetCellBackgroundColour(i, j, wx.Colour(255, 99, 71))  # 浅红色
        # 自动调整每一列和每一行的大小以适应内容
        self.grid.AutoSizeColumns()
        self.grid.AutoSizeRows()
        # 添加重置按钮
        self.grid.InsertCols(0)
        cols_title.insert(0, "重置按钮")
        for i in range(len(self.testCases)):
            self.grid.SetCellRenderer(i, 0, ResetButtonRenderer())

        self.grid.Bind(wx.grid.EVT_GRID_CELL_LEFT_CLICK, self.on_reset_click)

        # 创建下载按钮
        download_button = wx.Button(dialog, label="下载")
        download_button.Bind(wx.EVT_BUTTON, lambda evt: self.on_download(self.grid, evt))

        # 创建对话框的布局管理器，并将grid添加到其中
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.grid, 1, wx.EXPAND | wx.ALL)
        sizer.Add(download_button, 0, wx.ALIGN_CENTER | wx.ALL, 10)
        dialog.SetSizer(sizer)

        # 显示对话框
        dialog.ShowModal()
        dialog.Destroy()

    def reset_grid(self, grid):
        # 清除原有数据
        grid.ClearGrid()
        # 获取新的数据
        data = http_manager.get_params(f'/get_cases_by_case_id/{self.CaseID}')
        all_case = data.get('cases')
        for i, case in enumerate(all_case):
            for j, item in enumerate(case[:-2]):  # 排除用例ID
                grid.SetCellValue(i, j + 1, str(item))  # self.grid.InsertCols(0) 所以要j+1
        # 刷新网格以显示新的数据
        grid.ForceRefresh()

    def on_reset_click(self, evt):
        row, col = evt.GetRow(), evt.GetCol()
        # Check if "Reset" cell has been clicked
        if col == 0:
            case_id = self.case_row_to_id[row]
            reset_msg = wx.MessageDialog(self, '您确定要重置这条用例测试结果吗?', '确认', wx.YES_NO | wx.ICON_QUESTION)
            reset_response = reset_msg.ShowModal()
            if reset_response == wx.ID_YES:
                logger.info(f"重置ID: {case_id} 的用例测试状态")
                http_manager.post_data('/reset_case_result', {'case_id': case_id})
                evt.Skip(False)
                self.reset_grid(self.grid)  # 刷新网格布局
                wx.CallAfter(self.refresh_node_case_status, case_id=case_id)
                wx.CallAfter(self.update_statistics)
                self.tree.Refresh()
            reset_msg.Destroy()
            return
        evt.Skip(True)

    def select_annex(self, event):
        pass

    def on_download(self, grid, event):
        """
        下载用例
        :param grid:
        :param event:
        :return:
        """
        logger.info("----------------开始下载用例测试结果-----------------")
        # 获取Windows下载目录路径
        downloads_path = os.path.join(os.path.expanduser('~'), 'Downloads')
        # 设置文件名和路径
        now = datetime.now()
        formatted_now = now.strftime('%Y_%m_%d_%H_%M_%S')
        filename = f"PATVS_result_{formatted_now}.xlsx"
        filepath = os.path.join(downloads_path, filename)

        # 创建一个Workbook和一个Worksheet
        wb = openpyxl.Workbook()
        ws = wb.active

        # 设置列标题
        cols_title = ['测试结果', '测试耗时(S)', '选择次数', '测试机型', '用例标题', '前置条件', '用例步骤', '预期结果',
                      '开始时间', '完成时间', '测试动作', '评论']
        # 创建一个加粗的字体
        bold_font = Font(bold=True)
        ws.append(cols_title)
        for cell in ws["1:1"]:
            cell.font = bold_font
        # 填充数据
        for row in range(grid.GetNumberRows()):
            row_data = [grid.GetCellValue(row, col) for col in range(1, grid.GetNumberCols())]  # 排除第一列
            ws.append(row_data)

            # 根据测试结果设置单元格背景颜色
            if row_data[0] == 'Pass':
                for cell in ws[row + 2]:  # Excel行列都是从1开始计数，标题行占据第1行
                    cell.fill = PatternFill(start_color="90EE90", end_color="90EE90", fill_type="solid")
            elif row_data[0] == 'Fail' or row_data[0] == 'Block':
                for cell in ws[row + 2]:
                    cell.fill = PatternFill(start_color="FF6347", end_color="FF6347", fill_type="solid")

        # 保存文件
        try:
            wb.save(filepath)
            wx.MessageBox(f"文件已成功保存至 {filepath}", "保存成功", wx.OK | wx.ICON_INFORMATION)
        except IOError as e:
            wx.LogError(f"无法保存文件 '{filepath}'. 错误: {e}")

    def PopulateTree(self, sheet_id, sheet_name):
        """
        负责展示用例左侧节点
        :param sheet_id: 用例文件
        :return: 所有用例内容
        """
        logger.warning(11111111111111111111111)
        logger.warning(sheet_id)
        logger.warning(sheet_name)
        logger.warning(222222222222222222222222)
        self.tree.DeleteAllItems()  # 清空现有的树状结构
        all_case = http_manager.get_cases_by_sheet_id(sheet_id)
        self.update_statistics()
        # 定义用于表示状态的图标
        icons = {
            "Pass": resource_path("icon\\Pass.png"),
            "Fail": resource_path("icon\\Fail.png"),
            "Block": resource_path("icon\\Block.png"),
            "None": None,
            "Root": resource_path("icon\\rootIcon.png")
        }
        image_list = wx.ImageList(16, 16)
        self.icon_indices = {}
        # 创建一个透明位图
        transparent_bmp = wx.Bitmap(16, 16, 32)
        image = transparent_bmp.ConvertToImage()
        image.InitAlpha()
        for x in range(16):
            for y in range(16):
                image.SetAlpha(x, y, 0)
        transparent_bmp = wx.Bitmap(image)
        for status, icon in icons.items():
            if icon:
                self.icon_indices[status] = image_list.Add(wx.Bitmap(icon))  # 逐个向图像列表中添加图标，并获取其索引
            else:
                self.icon_indices[status] = image_list.Add(transparent_bmp)
        self.tree.AssignImageList(image_list)  # 将图像列表分配给树

        # 添加根节点并设置图标
        root = self.tree.AddRoot(sheet_name, self.icon_indices['Root'])

        for row in all_case:
            caseStatus = row[0]
            caseID = row[12]
            # 按照 机型→标题 展示title
            caseModel = (row[3] + '→') if row[3] else ''
            caseTitle = row[4]
            caseSteps = row[6]
            expectedResult = row[7]

            # 根据状态添加相应的图标
            if caseStatus in self.icon_indices:
                caseNode = self.tree.AppendItem(root, caseModel + caseTitle)
                self.tree.SetItemImage(caseNode, self.icon_indices[caseStatus])  # 设置节点图像
            else:
                caseNode = self.tree.AppendItem(root, caseModel + caseTitle)

            # 将CaseID存储在节点数据中
            self.tree.SetItemData(caseNode, caseID)
            stepsNode = self.tree.AppendItem(caseNode, f"操作步骤: {caseSteps}")
            self.tree.SetItemData(stepsNode, caseID)
            resultNode = self.tree.AppendItem(caseNode, f"预期结果: {expectedResult}")
            self.tree.SetItemData(resultNode, caseID)

        self.tree.Expand(root)
        return all_case

    def OnSelChanged(self, event):
        """
        负责展示用例详情
        :param event:
        :return:
        """
        item = event.GetItem()
        parent = self.tree.GetItemParent(item)

        # 根节点不展示内容
        if self.tree.GetItemText(item) == self.sheet_name:
            self.content.SetValue("")
            self.CaseID = None
            return

        # 获取节点的CaseID
        self.CaseID = self.tree.GetItemData(item)
        logger.info(f"You selected the case with ID: {self.CaseID}")

        for case in self.testCases:
            if case[12] == self.CaseID:
                self.content.Clear()
                self.log_content.Clear()
                self.content.SetValue(f"测试机型: {case[3]}\n\n")
                self.content.AppendText(f"用例标题:\n{case[4]}\n\n")
                self.content.AppendText(f"前置条件:\n{case[5]}\n\n")
                self.content.AppendText(f"操作步骤:\n{case[6]}\n\n")
                self.content.SetInsertionPointEnd()  # 移动光标到末尾以便于添加蓝色文本
                self.content.SetDefaultStyle(wx.TextAttr(wx.BLUE))
                self.content.AppendText(f"预期结果:\n{case[7]}")
                # 再次将文本颜色设置回默认颜色，以防止后续文本也变为蓝色
                self.content.SetDefaultStyle(wx.TextAttr(wx.BLACK))
                wx.CallAfter(self.scroll_to_top)  # 调用滚动方法
                break

    def scroll_to_top(self):
        """
        滚动到文本框的顶部
        """
        self.content.ScrollLines(-self.content.GetNumberOfLines())

# -*- coding: utf-8 -*-
# 负责GUI界面展示以及交互逻辑

import wx
import matplotlib.pyplot as plt
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from requests_manager.http_requests_manager import http_manager
from common.logs import logger


class CountPanel(wx.Panel):
    def __init__(self, parent):
        super(CountPanel, self).__init__(parent)
        self.figure = plt.figure()
        self.canvas = FigureCanvas(self, -1, self.figure)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.canvas, 1, wx.EXPAND)
        self.SetSizer(sizer)

    def update_case_counts(self, data):
        self.figure.clear()
        ax = self.figure.add_subplot(111)

        labels = ['Total Cases', 'Executed Cases']
        values = [data['case_count'], data['executed_cases_count']]

        ax.bar(labels, values, color=['blue', 'green'])
        ax.set_ylabel('Count')
        ax.set_title('Test Case Counts')
        for i, v in enumerate(values):
            ax.text(i, v + 1, str(v), ha='center')

        self.canvas.draw()


class PercentagePanel(wx.Panel):
    def __init__(self, parent):
        super(PercentagePanel, self).__init__(parent)
        self.figure = plt.figure()
        self.canvas = FigureCanvas(self, -1, self.figure)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.canvas, 1, wx.EXPAND)
        self.SetSizer(sizer)

    def update_percentages(self, data):
        self.figure.clear()
        ax = self.figure.add_subplot(111)

        labels = ['Pass Rate', 'Fail Rate', 'Block Rate', 'Not Executed']
        pass_rate = float(data['pass_rate'].strip('%'))
        fail_rate = float(data['fail_rate'].strip('%'))
        block_rate = float(data['block_rate'].strip('%'))
        not_executed = 100 - pass_rate - fail_rate - block_rate  # 计算未执行的百分比

        values = [pass_rate, fail_rate, block_rate, not_executed]
        colors = ['green', 'red', 'gray', 'blue']  # 指定颜色

        ax.pie(values, labels=labels, autopct='%1.1f%%', startangle=140, colors=colors)
        ax.set_title('Test Case Percentages')

        self.canvas.draw()


class TimePanel(wx.Panel):
    def __init__(self, parent):
        super(TimePanel, self).__init__(parent)
        self.figure = plt.figure()
        self.canvas = FigureCanvas(self, -1, self.figure)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.canvas, 1, wx.EXPAND)
        self.SetSizer(sizer)

    def update_time_counts(self, data):
        self.figure.clear()
        ax = self.figure.add_subplot(111)

        labels = ['Execution Time', 'Plan Time']
        values = [data['case_time_count'], data['workloading_time']]

        ax.bar(labels, values, color=['blue', 'green'])
        ax.set_ylabel('Time (Min)')
        ax.set_title('Test Case Time Counts')
        for i, v in enumerate(values):
            ax.text(i, v + 1, str(v), ha='center')

        self.canvas.draw()


class TestAdminPanel(wx.Panel):
    def __init__(self, parent, token):
        super().__init__(parent)
        self.token = token
        # 创建主布局
        mainSizer = wx.BoxSizer(wx.VERTICAL)

        # 用例筛选下拉框
        try:
            data = http_manager.get_params('/get_plan_names_by_admin')
            plan_names = data.get('plan_names')
        except Exception as e:
            wx.MessageBox(f'未知错误: {str(e)}', 'Error', wx.OK | wx.ICON_ERROR)
            plan_names = []
        self.plan_name_combo = wx.ComboBox(self, choices=plan_names)
        self.plan_name_combo.Bind(wx.EVT_COMBOBOX, self.on_plan_select)

        # 添加新的下拉框用于显示 sheet_name
        self.sheet_name_combo = wx.ComboBox(self)
        self.sheet_name_combo.Bind(wx.EVT_COMBOBOX, self.on_sheet_select)

        # 创建一个水平盒子来放置 case_search_combo 下拉框
        caseSearchSizer = wx.BoxSizer(wx.HORIZONTAL)

        self.planLabel = wx.StaticText(self, label="测试计划")
        caseSearchSizer.Add(self.planLabel, 0, wx.ALL, 5)
        caseSearchSizer.Add(self.plan_name_combo, 0, wx.ALL, 5)

        self.sheetLabel = wx.StaticText(self, label="测试用例")
        caseSearchSizer.Add(self.sheetLabel, 0, wx.ALL, 5)
        caseSearchSizer.Add(self.sheet_name_combo, 0, wx.ALL, 5)

        self.testerLabel = wx.StaticText(self, label="测试人员:")
        caseSearchSizer.Add(self.testerLabel, 0, wx.ALL, 5)

        mainSizer.Add(caseSearchSizer, 0, wx.EXPAND)

        # 创建一个 notebook，用于添加多个面板
        self.notebook = wx.Notebook(self)
        self.count_panel = CountPanel(self.notebook)
        self.percentage_panel = PercentagePanel(self.notebook)
        self.case_time_panel = TimePanel(self.notebook)
        self.notebook.AddPage(self.count_panel, "CaseCounts")
        self.notebook.AddPage(self.percentage_panel, "Percentages")
        self.notebook.AddPage(self.case_time_panel, "TimeCounts")
        mainSizer.Add(self.notebook, 1, wx.EXPAND)

        self.SetSizer(mainSizer)

    def on_plan_select(self, event):
        # 选择测试计划后，更新用例表下拉框和测试人员
        plan_name = self.plan_name_combo.GetValue()
        try:
            plan_id = http_manager.get_params(f'/get_plan_id/{plan_name}').get('plan_id')
            sheet_names_with_ids = http_manager.get_params(f'/get_sheet_names_by_admin/{plan_name}').get(
                'sheet_names_with_ids')

            # 清空并重新填充 sheet_name_combo
            self.sheet_name_combo.Clear()
            for sheet_id, sheet_name in sheet_names_with_ids:
                self.sheet_name_combo.Append(sheet_name, sheet_id)

            # 更新测试人员
            self.update_tester_label(plan_name=plan_name)

            # 获取并显示统计数据
            data = http_manager.get_params(f'/calculate_plan_statistics/{plan_id}').get('result')
            self.count_panel.update_case_counts(data)
            self.percentage_panel.update_percentages(data)
            self.case_time_panel.update_time_counts(data)
        except Exception as e:
            wx.MessageBox(f'未知错误: {str(e)}', 'Error', wx.OK | wx.ICON_ERROR)

    def on_sheet_select(self, event):
        # 选择用例表后，更新测试人员和可视化内容
        selected_index = self.sheet_name_combo.GetSelection()
        if selected_index != wx.NOT_FOUND:
            sheet_id = self.sheet_name_combo.GetClientData(selected_index)
            sheet_name = self.sheet_name_combo.GetString(selected_index)
            try:
                # 更新测试人员
                self.update_tester_label(sheet_id=sheet_id)

                # 获取并显示统计数据
                data = http_manager.get_params(f'/calculate_progress_and_pass_rate/{sheet_id}').get('result')
                self.count_panel.update_case_counts(data)
                self.percentage_panel.update_percentages(data)
                self.case_time_panel.update_time_counts(data)
            except Exception as e:
                wx.MessageBox(f'未知错误: {str(e)}', 'Error', wx.OK | wx.ICON_ERROR)

    def update_tester_label(self, plan_name=None, sheet_id=None):
        try:
            testers = http_manager.get_params('/get_tester', params={'plan_name': plan_name, 'sheet_id': sheet_id}).get(
                'tester')
            logger.warning(testers)
            self.testerLabel.SetLabel(f"测试人员: {testers}")
        except Exception as e:
            wx.MessageBox(f'未知错误: {str(e)}', 'Error', wx.OK | wx.ICON_ERROR)

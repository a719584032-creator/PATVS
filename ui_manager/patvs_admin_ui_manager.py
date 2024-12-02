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
    def __init__(self, parent, username, token):
        super().__init__(parent)
        self.username = username  # 保存用户名
        self.token = token
        self.userid = http_manager.get_params(f'/get_userid/{self.username}').get('user_id')  # 保存用户名
        # 创建主布局
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        # 用例筛选下拉框
        # 固定宽度
        fixed_width = 200
        self.project_name_combo = wx.ComboBox(self)
        self.project_name_combo.SetMinSize(wx.Size(150, -1))
        self.project_name_combo.Bind(wx.EVT_COMBOBOX, self.on_project_select)
        self.project_name_combo.Bind(wx.EVT_MOTION, self.on_project_hover)  # 鼠标悬停时动态加载数据

        self.plan_name_combo = wx.ComboBox(self)
        self.plan_name_combo.SetMinSize(wx.Size(fixed_width, -1))
        self.plan_name_combo.Bind(wx.EVT_COMBOBOX, self.on_plan_select)
        self.plan_name_combo.Bind(wx.EVT_MOTION, self.on_plan_hover)

        self.model_name_combo = wx.ComboBox(self)
        self.model_name_combo.SetMinSize(wx.Size(fixed_width, -1))
        self.model_name_combo.Bind(wx.EVT_COMBOBOX, self.on_model_select)
        self.model_name_combo.Bind(wx.EVT_MOTION, self.on_model_hover)

        self.sheet_name_combo = wx.ComboBox(self)
        self.sheet_name_combo.SetMinSize(wx.Size(fixed_width, -1))
        self.sheet_name_combo.Bind(wx.EVT_COMBOBOX, self.on_sheet_select)
        self.sheet_name_combo.Bind(wx.EVT_MOTION, self.on_sheet_hover)

        # 创建一个水平盒子来放置 case_search_combo 下拉框
        caseSearchSizer = wx.BoxSizer(wx.HORIZONTAL)

        self.projectLabel = wx.StaticText(self, label="项目")
        caseSearchSizer.Add(self.projectLabel, 0, wx.ALL, 5)
        caseSearchSizer.Add(self.project_name_combo, 0, wx.ALL, 5)

        self.planLabel = wx.StaticText(self, label="测试计划")
        caseSearchSizer.Add(self.planLabel, 0, wx.ALL, 5)
        caseSearchSizer.Add(self.plan_name_combo, 0, wx.ALL, 5)

        self.modelLabel = wx.StaticText(self, label="测试机型")
        caseSearchSizer.Add(self.modelLabel, 0, wx.ALL, 5)
        caseSearchSizer.Add(self.model_name_combo, 0, wx.ALL, 5)

        self.sheetLabel = wx.StaticText(self, label="测试用例")
        caseSearchSizer.Add(self.sheetLabel, 0, wx.ALL, 5)
        caseSearchSizer.Add(self.sheet_name_combo, 0, wx.ALL, 5)

        #  caseSearchSizer.Add(self.modify_button, 0, wx.CENTER | wx.ALL, 5)

        mainSizer.Add(caseSearchSizer, 0, wx.EXPAND)
        # 新增一行放置测试人员、项目、预估时间的 Label
        infoSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.testerLabel = wx.StaticText(self, label="测试人员:")
        self.timeLabel = wx.StaticText(self, label="预估时间:")
        # 添加修改按钮
        self.modify_button = wx.Button(self, label="修改")
        self.modify_button.Bind(wx.EVT_BUTTON, self.on_modify)

        infoSizer.Add(self.testerLabel, 0, wx.ALL, 5)
        infoSizer.AddSpacer(100)
        infoSizer.Add(self.timeLabel, 0, wx.ALL, 5)
        infoSizer.AddSpacer(100)
        infoSizer.Add(self.modify_button, 0, wx.CENTER | wx.ALL, 5)
        mainSizer.Add(infoSizer, 0, wx.EXPAND)

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

    def on_project_select(self, event):
        logger.warning("开始调用 on_project_select")
        # 获取选择的项目名称
        project_name = self.project_name_combo.GetValue()

        # 根据项目名称获取计划名称
        plan_names_with_ids = http_manager.get_plan_names(self.userid, project_name)

        # 清空并重新填充 plan_name_combo
        self.plan_name_combo.Clear()
        for plan_id, plan_name in plan_names_with_ids:
            self.plan_name_combo.Append(plan_name, plan_id)

        # 清空 sheet_name_combo，因为项目改变可能导致计划和用例表的变化
        self.model_name_combo.Clear()
        self.sheet_name_combo.Clear()
        logger.warning("结束调用 on_project_select")

    def on_model_select(self, event):
        # 选择测试计划后，更新测试机型
        logger.warning('开始调用 model select')
        selected_index = self.model_name_combo.GetSelection()
        if selected_index != wx.NOT_FOUND:
            self.model_id = self.model_name_combo.GetClientData(selected_index)
            self.model_name = self.model_name_combo.GetString(selected_index)
            logger.warning(self.model_id)
            logger.warning(self.model_name)
        sheet_names_with_ids = http_manager.get_sheet_names(self.plan_id)
        # 清空并重新填充 sheet_name_combo
        self.sheet_name_combo.Clear()
        for sheet_id, sheet_name in sheet_names_with_ids:
            self.sheet_name_combo.Append(sheet_name, sheet_id)
        logger.warning('调用 model select 结束')

    def on_project_hover(self, event):
        """
        当鼠标悬停在项目下拉框时，动态加载项目数据，同时保留当前选中的项目
        """
        logger.info("开始动态加载项目数据")
        try:
            # 获取当前选中的项目名称
            current_selection = self.project_name_combo.GetValue()

            # 调用接口获取最新的项目名称列表
            project_names = http_manager.get_params(f'/get_project_names/{self.userid}').get('project_names', [])

            # 清空并重新填充 project_name_combo
            self.project_name_combo.Clear()
            for project_name in project_names:
                self.project_name_combo.Append(project_name)

            # 如果之前有选中的项目，尝试重新设置选中状态
            if current_selection in project_names:
                self.project_name_combo.SetValue(current_selection)
            else:
                # 如果当前选中的项目不在最新列表中，清空选中状态
                self.project_name_combo.SetValue("")

            logger.info("项目数据加载完成")
        except Exception as e:
            logger.error(f"加载项目数据失败: {e}")
        event.Skip()

    def on_model_hover(self, event):
        # 获取当前选择的内容
        selection = self.model_name_combo.GetStringSelection()
        if selection:
            self.model_name_combo.SetToolTip(selection)
        event.Skip()

    def on_plan_hover(self, event):
        # 获取当前选择的内容
        selection = self.plan_name_combo.GetStringSelection()
        if selection:
            self.plan_name_combo.SetToolTip(selection)
        event.Skip()

    def on_sheet_hover(self, event):
        # 获取当前选择的内容
        selection = self.sheet_name_combo.GetStringSelection()
        if selection:
            self.sheet_name_combo.SetToolTip(selection)
        event.Skip()

    def on_plan_select(self, event):
        # 选择测试计划后，更新用例表下拉框和测试人员
        logger.warning('开始调用 plan select')
        selected_index = self.plan_name_combo.GetSelection()
        if selected_index != wx.NOT_FOUND:
            self.plan_id = self.plan_name_combo.GetClientData(selected_index)
            self.plan_name = self.plan_name_combo.GetString(selected_index)
        model_names_with_ids = http_manager.get_params(f'/get_model_names/{self.plan_id}').get('model_names')
        data = http_manager.get_params(f'/calculate_plan_statistics/{self.plan_id}').get('result')
        # 清空并重新填充 model_name_combo
        self.model_name_combo.Clear()
        self.sheet_name_combo.Clear()
        for model_id, model_name in model_names_with_ids:
            self.model_name_combo.Append(model_name, model_id)
            # 更新测试人员和图表
        self.update_tester_label(data)
        self.count_panel.update_case_counts(data)
        self.percentage_panel.update_percentages(data)
        self.case_time_panel.update_time_counts(data)


    def on_sheet_select(self, event):
        # 选择用例表后，更新测试人员和可视化内容
        selected_index = self.sheet_name_combo.GetSelection()
        if selected_index != wx.NOT_FOUND:
            self.sheet_id = self.sheet_name_combo.GetClientData(selected_index)
            self.sheet_name = self.sheet_name_combo.GetString(selected_index)
            try:
                # 获取并显示统计数据
                pamars = {'planId': self.plan_id, 'modelId': self.model_id, 'sheetId': self.sheet_id}
                data = http_manager.get_params(f'/calculate_progress_and_pass_rate', params=pamars).get('result')
                # 更新测试人员及图表
                self.update_tester_label(data)
                self.count_panel.update_case_counts(data)
                self.percentage_panel.update_percentages(data)
                self.case_time_panel.update_time_counts(data)
            except Exception as e:
                wx.MessageBox(f'未知错误: {str(e)}', 'Error', wx.OK | wx.ICON_ERROR)

    def update_tester_label(self, data):
        try:
            self.testerLabel.SetLabel(f"测试人员: {data['tester']}")
            self.timeLabel.SetLabel(f"预估时间: {data['workloading_time']} 分钟")
        except Exception as e:
            wx.MessageBox(f'未知错误: {str(e)}', 'Error', wx.OK | wx.ICON_ERROR)

    def on_modify(self, event):
        plan_name = self.plan_name_combo.GetValue()
        sheet_name = self.sheet_name_combo.GetValue()

        if not plan_name:  # 如果未选择测试计划
            wx.MessageBox('请先选择一个测试计划', '提示', wx.OK | wx.ICON_WARNING)
            return

        if sheet_name:  # 如果选择了测试用例表
            selected_index = self.sheet_name_combo.GetSelection()
            sheet_id = self.sheet_name_combo.GetClientData(selected_index)
            modify_dialog = ModifyDialog(self, "修改 Sheet 信息", plan_name, sheet_name, sheet_id)
        else:  # 只选择了测试计划
            modify_dialog = ModifyDialog(self, "修改测试计划信息", plan_name)

        if modify_dialog.ShowModal() == wx.ID_OK:
            new_data = modify_dialog.get_values()
            try:
                if sheet_name:
                    data = {
                        'plan_name': plan_name,
                        'sheet_id': sheet_id,
                        'tester': new_data['tester'],
                        'project': new_data['project'],
                        'workloading': new_data['workloading'] + '(Min)',
                    }
                else:
                    data = {
                        'plan_name': plan_name,
                        'tester': new_data['tester'],
                        'project': new_data['project'],
                        'workloading': new_data['workloading'] + '(Min)',
                    }
                logger.warning(data)
                http_manager.post_data('/update_project_workloading_tester', data=data, token=self.token)
                self.on_plan_select(plan_name)
                wx.MessageBox('修改成功', '提示', wx.OK | wx.ICON_INFORMATION)
            except Exception as e:
                wx.MessageBox(f'修改失败: {str(e)}', '错误', wx.OK | wx.ICON_ERROR)

        modify_dialog.Destroy()


class ModifyDialog(wx.Dialog):
    def __init__(self, parent, title, plan_name, sheet_name=None, sheet_id=None):
        super().__init__(parent, title=title, size=(300, 250))
        panel = wx.Panel(self)
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # 仅添加一次的控件，不重复
        plan_label = wx.StaticText(panel, label=f"测试计划: {plan_name}")
        main_sizer.Add(plan_label, 0, wx.ALL, 5)

        if sheet_name:  # 如果有测试用例表，添加显示
            sheet_label = wx.StaticText(panel, label=f"测试用例表: {sheet_name}")
            main_sizer.Add(sheet_label, 0, wx.ALL, 5)

        # 创建静态文本和输入框
        tester_label = wx.StaticText(panel, label="测试人员:")
        self.tester = wx.TextCtrl(panel, value="", size=(200, -1))
        self.tester.SetHint("请输入测试人员，为空表示不修改")
        main_sizer.Add(tester_label, 0, wx.ALL, 5)
        main_sizer.Add(self.tester, 0, wx.EXPAND | wx.ALL, 5)

        project_label = wx.StaticText(panel, label="项目:")
        self.project = wx.TextCtrl(panel, value="", size=(200, -1))
        self.project.SetHint("请输入项目，为空表示不修改")
        main_sizer.Add(project_label, 0, wx.ALL, 5)
        main_sizer.Add(self.project, 0, wx.EXPAND | wx.ALL, 5)

        workloading_label = wx.StaticText(panel, label="预估时间(min):")
        self.workloading = wx.TextCtrl(panel, value="", size=(200, -1), style=wx.TE_PROCESS_ENTER)
        self.workloading.SetHint("请输入预估时间(min)，为空表示不修改")
        self.workloading.Bind(wx.EVT_CHAR, self.on_char)  # 绑定输入事件，限制输入为数字
        main_sizer.Add(workloading_label, 0, wx.ALL, 5)
        main_sizer.Add(self.workloading, 0, wx.EXPAND | wx.ALL, 5)

        # OK 和 Cancel 按钮
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)  # 修正此处
        ok_button = wx.Button(panel, wx.ID_OK, label="确定")
        cancel_button = wx.Button(panel, wx.ID_CANCEL, label="取消")
        button_sizer.Add(ok_button, 0, wx.ALL, 5)
        button_sizer.Add(cancel_button, 0, wx.ALL, 5)

        main_sizer.Add(button_sizer, 0, wx.ALIGN_CENTER | wx.ALL, 5)

        # 将布局设置到 panel 上
        panel.SetSizer(main_sizer)
        panel.Layout()  # 强制更新布局

        self.SetSize((400, 400))  # 手动设置窗口大小以避免过小
        self.Centre()  # 窗口居中

        self.plan_name = plan_name
        self.sheet_name = sheet_name
        self.sheet_id = sheet_id

    def get_values(self):
        return {
            'tester': self.tester.GetValue(),
            'project': self.project.GetValue(),
            'workloading': self.workloading.GetValue(),
        }

    def on_char(self, event):
        # 仅允许数字输入
        keycode = event.GetKeyCode()
        if chr(keycode).isdigit() or keycode == wx.WXK_BACK:
            event.Skip()  # 允许数字输入和删除键
        else:
            return  # 阻止其他字符输入

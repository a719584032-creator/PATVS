# -*- coding: utf-8 -*-
# 负责GUI界面展示以及交互逻辑

import wx
import wx.grid
import matplotlib.pyplot as plt
import os
import webbrowser
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
        # 添加查看详情按钮
        self.view_button = wx.Button(self, label="查看详情")
        self.view_button.Bind(wx.EVT_BUTTON, self.check_status)
        # 添加修改按钮
        self.modify_button = wx.Button(self, label="修改人员")
        self.modify_button.Bind(wx.EVT_BUTTON, self.on_modify)

        self.modify_case_title_button = wx.Button(self, label="修改用例标题")
        self.modify_case_title_button.Bind(wx.EVT_BUTTON, self.on_modify_case_title)

        self.add_user_button = wx.Button(self, label="添加用户")
        self.add_user_button.Bind(wx.EVT_BUTTON, self.add_user)

        infoSizer.Add(self.testerLabel, 0, wx.ALL, 5)
        infoSizer.AddSpacer(100)
        infoSizer.Add(self.timeLabel, 0, wx.ALL, 5)
        infoSizer.AddSpacer(100)
        infoSizer.Add(self.view_button, 0, wx.CENTER | wx.ALL, 5)
        infoSizer.Add(self.modify_button, 0, wx.CENTER | wx.ALL, 5)
        infoSizer.Add(self.modify_case_title_button, 0, wx.CENTER | wx.ALL, 5)
        infoSizer.Add(self.add_user_button, 0, wx.CENTER | wx.ALL, 5)
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
        project_name = self.project_name_combo.GetValue()
        plan_name = self.plan_name_combo.GetValue()

        if not plan_name:  # 如果未选择测试计划
            wx.MessageBox('请先选择一个测试计划', '提示', wx.OK | wx.ICON_WARNING)
            return

        # 确保 plan_id 已定义
        if not hasattr(self, 'plan_id'):
            wx.MessageBox('请先选择一个有效的测试计划', '提示', wx.OK | wx.ICON_WARNING)
            return

        # 创建修改对话框，只用于修改测试计划
        modify_dialog = ModifyDialog(self, "修改测试计划信息", project_name, plan_name)

        if modify_dialog.ShowModal() == wx.ID_OK:
            new_data = modify_dialog.get_values()
            try:
                # 创建要发送的数据
                data = {
                    'plan_id': self.plan_id,
                    'tester': new_data['tester'],
                    'workloading': new_data['workloading']
                }

                logger.warning(data)
                response = http_manager.post_data('/update_project_workloading_tester', data=data, token=self.token)

                # 重新加载数据
                # 创建一个模拟的事件对象
                mock_event = wx.CommandEvent(wx.wxEVT_COMMAND_COMBOBOX_SELECTED)
                self.on_plan_select(mock_event)

                wx.MessageBox('修改成功', '提示', wx.OK | wx.ICON_INFORMATION)
            except Exception as e:
                wx.MessageBox(f'修改失败: {str(e)}', '错误', wx.OK | wx.ICON_ERROR)

        modify_dialog.Destroy()

    def check_status(self, event):
        if not self.sheet_id or not self.model_id:
            wx.MessageBox('请先选择用例', 'Warning')
            return

        # 获取用例数据
        self.testCases = http_manager.get_cases_by_sheet_id(self.sheet_id, self.model_id)

        # 创建一个新的对话框，并且允许对话框最大化
        dialog = wx.Dialog(self, title="查看用例状态", size=(800, 600), style=wx.MAXIMIZE_BOX | wx.DEFAULT_DIALOG_STYLE)

        # 创建grid并设置行和列
        self.grid = wx.grid.Grid(dialog)
        self.grid.CreateGrid(numRows=len(self.testCases), numCols=13)  # 增加两列用于按钮

        # 设置列标题
        cols_title = ['重置按钮', '测试结果', '测试耗时(S)', '用例标题', '前置条件',
                      '用例步骤', '预期结果', '开始时间', '完成时间', '评论', '失败次数', '阻塞次数', '查看图片']
        for i, title in enumerate(cols_title):
            self.grid.SetColLabelValue(i, title)

        # 填充数据
        self.row_to_execution_id = {}
        for i, case in enumerate(self.testCases):
            execution_id = case.get('ExecutionID')
            if execution_id is not None:
                self.row_to_execution_id[i] = execution_id  # 记录行号与 ExecutionID 的映射

            # 根据列标题填充数据
            self.grid.SetCellValue(i, 1, str(case.get('TestResult', "")))
            self.grid.SetCellValue(i, 2, str(case.get('TestTime', "")))
            self.grid.SetCellValue(i, 3, case.get('CaseTitle', ""))
            self.grid.SetCellValue(i, 4, str(case.get('PreConditions', "")))
            self.grid.SetCellValue(i, 5, case.get('CaseSteps', ""))
            self.grid.SetCellValue(i, 6, case.get('ExpectedResult', ""))
            self.grid.SetCellValue(i, 7, str(case.get('StartTime', "") or ""))
            self.grid.SetCellValue(i, 8, str(case.get('EndTime', "") or ""))
            self.grid.SetCellValue(i, 9, str(case.get('Comment', "") or ""))
            self.grid.SetCellValue(i, 10, str(case.get('FailCount', "") or ""))
            self.grid.SetCellValue(i, 11, str(case.get('BlockConut', "") or ""))

            # 设置背景颜色
            test_result = case.get('TestResult', "")
            if test_result == 'Pass':
                self.grid.SetCellBackgroundColour(i, 1, wx.Colour(144, 238, 144))  # 浅绿色
            elif test_result in ['Fail', 'Block']:
                self.grid.SetCellBackgroundColour(i, 1, wx.Colour(255, 99, 71))  # 浅红色

            # 为最后一列设置“查看图片按钮”
            self.grid.SetCellValue(i, 12, "查看图片")
            self.grid.SetCellRenderer(i, 12, ButtonRenderer("查看图片"))

        # 禁止直接编辑单元格
        self.grid.EnableEditing(False)

        # 绑定单元格点击事件
        self.grid.Bind(wx.grid.EVT_GRID_CELL_LEFT_CLICK, self.on_cell_click)
        # 自动调整每一列和每一行的大小以适应内容
        self.grid.AutoSizeColumns()
        self.grid.AutoSizeRows()

        # 创建对话框的布局管理器，并将grid添加到其中
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.grid, 1, wx.EXPAND | wx.ALL)
        dialog.SetSizer(sizer)

        # 显示对话框
        dialog.ShowModal()
        dialog.Destroy()

    def on_cell_click(self, event):
        """处理单元格点击事件"""
        row = event.GetRow()
        col = event.GetCol()
        # 判断点击的是“查看图片”列
        if col == 12:
            execution_id = self.row_to_execution_id.get(row)
            if execution_id:
                self.on_view_image_click(execution_id)

        # 继续处理其他事件
        event.Skip()

    def on_view_image_click(self, execution_id):
        """查看与 ExecutionID 相关的图片，生成 HTML 文件展示图片和信息"""

        # 调用接口获取图片
        response = http_manager.get_params(f'/get_images/{execution_id}')
        images = response.get('images', [])
        if not images:
            logger.warning(f"No images found for Execution ID {execution_id}: {response}")
            wx.MessageBox('未找到相关图片', 'Info')
            return

        # 生成 HTML 内容
        html_content = f"""
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Execution ID {execution_id} 图片预览</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    margin: 20px;
                    line-height: 1.6;
                }}
                h1 {{
                    text-align: center;
                    color: #333;
                }}
                .image-card {{
                    margin-bottom: 30px;
                    border: 1px solid #ddd;
                    padding: 15px;
                    border-radius: 8px;
                    box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
                }}
                .image-info {{
                    margin-bottom: 15px;
                }}
                .image-info p {{
                    margin: 5px 0;
                }}
                img {{
                    display: block;
                    max-width: 100%;
                    height: auto;
                    margin: 0 auto;
                    border: 1px solid #ccc;
                    border-radius: 5px;
                }}
            </style>
        </head>
        <body>
            <h1>Execution ID {execution_id} 图片预览</h1>
        """

        for index, image in enumerate(images):
            url = image.get('url')
            file_name = image.get('original_file_name', '未知文件名')
            file_size = image.get('file_size', '未知大小')
            mime_type = image.get('mime_type', '未知类型')
            image_time = image.get('time', '未知时间')

            if not url:
                logger.warning(f"Image URL missing for Execution ID {execution_id} at index {index}")
                continue

            # 添加图片和信息到 HTML
            html_content += f"""
            <div class="image-card">
                <div class="image-info">
                    <p><strong>图片 {index + 1} 信息:</strong></p>
                    <p>文件名: {file_name}</p>
                    <p>文件大小: {file_size} 字节</p>
                    <p>MIME 类型: {mime_type}</p>
                    <p>时间: {image_time}</p>
                    <p>URL: <a href="{url}" target="_blank">{url}</a></p>
                </div>
                <img src="{url}" alt="图片 {index + 1}">
            </div>
            """

        html_content += """
        </body>
        </html>
        """

        # 将 HTML 写入文件
        html_file = f"execution_{execution_id}_images.html"
        with open(html_file, "w", encoding="utf-8") as file:
            file.write(html_content)

        # 使用默认浏览器打开 HTML 文件
        html_path = os.path.abspath(html_file)
        webbrowser.open(f"file://{html_path}")
        logger.info(f"HTML file generated and opened in browser: {html_path}")

    def on_modify_case_title(self, event):
        # 检查是否选择了sheet和model
        if not hasattr(self, 'sheet_id') or not hasattr(self, 'model_id'):
            wx.MessageBox('请先选择用例', '提示')
            return

        # 获取用例数据（可复用check_status逻辑）
        case_list = http_manager.get_cases_by_sheet_id(self.sheet_id, self.model_id)
        # 只保留CaseID和CaseTitle
        case_simple = [{'CaseID': c['CaseID'], 'CaseTitle': c['CaseTitle']} for c in case_list]

        dialog = EditCaseTitleDialog(self, case_simple)
        if dialog.ShowModal() == wx.ID_OK:
            modified = dialog.get_modified_titles()
            changed = [c for c, ori in zip(modified, case_simple) if c['CaseTitle'] != ori['CaseTitle']]
            if changed:
                try:
                    data = {"cases": [{"case_id": item['CaseID'], "case_title": item['CaseTitle']} for item in changed]}
                    resp = http_manager.post_data('/modify/case_titles', data=data, token=self.token)
                    if resp and resp.get("success_count") == len(changed):
                        wx.MessageBox("全部修改成功！", "结果")
                    else:
                        wx.MessageBox(f"有部分修改失败，成功{resp.get('success_count', 0)}项", "结果")
                except Exception as e:
                    wx.MessageBox("批量修改失败", "错误")
            else:
                wx.MessageBox("没有需要修改的内容", "提示")
        dialog.Destroy()

    def add_user(self, event):
        dlg = AddUserDialog(self)
        if dlg.ShowModal() == wx.ID_OK:
            info = dlg.get_user_info()
            data = {
                "username": info["username"],
                "password": info["password"]
            }
            # 只有勾选了管理员才传role
            if info["is_admin"]:
                data["role"] = "admin"

            try:
                resp = http_manager.post_data("/add_user", data=data, token=self.token)
                if resp and resp.get("message"):
                    wx.MessageBox("用户添加成功！", "提示")
                else:
                    wx.MessageBox(f"添加失败: {resp.get('error', '未知错误')}", "错误")
            except Exception as e:
                wx.MessageBox(f"添加用户异常: {e}", "错误")
        dlg.Destroy()


class ModifyDialog(wx.Dialog):
    def __init__(self, parent, title, project_name, plan_name):
        super().__init__(parent, title=title, size=(300, 250))
        panel = wx.Panel(self)
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # 显示项目和计划信息
        project_label = wx.StaticText(panel, label=f"测试项目: {project_name}")
        main_sizer.Add(project_label, 0, wx.ALL, 5)

        plan_label = wx.StaticText(panel, label=f"测试计划: {plan_name}")
        main_sizer.Add(plan_label, 0, wx.ALL, 5)

        # 创建静态文本和输入框
        tester_label = wx.StaticText(panel, label="测试人员:")
        self.tester = wx.TextCtrl(panel, value="", size=(200, -1))
        self.tester.SetHint("请输入测试人员，为空表示不修改")
        main_sizer.Add(tester_label, 0, wx.ALL, 5)
        main_sizer.Add(self.tester, 0, wx.EXPAND | wx.ALL, 5)

        workloading_label = wx.StaticText(panel, label="预估时间(min):")
        self.workloading = wx.TextCtrl(panel, value="", size=(200, -1), style=wx.TE_PROCESS_ENTER)
        self.workloading.SetHint("请输入预估时间(min)，为空表示不修改")
        self.workloading.Bind(wx.EVT_CHAR, self.on_char)  # 绑定输入事件，限制输入为数字
        main_sizer.Add(workloading_label, 0, wx.ALL, 5)
        main_sizer.Add(self.workloading, 0, wx.EXPAND | wx.ALL, 5)

        # OK 和 Cancel 按钮
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        ok_button = wx.Button(panel, wx.ID_OK, label="确定")
        cancel_button = wx.Button(panel, wx.ID_CANCEL, label="取消")
        button_sizer.Add(ok_button, 0, wx.ALL, 5)
        button_sizer.Add(cancel_button, 0, wx.ALL, 5)

        main_sizer.Add(button_sizer, 0, wx.ALIGN_CENTER | wx.ALL, 5)

        # 将布局设置到 panel 上
        panel.SetSizer(main_sizer)
        panel.Layout()  # 强制更新布局

        self.SetSize((400, 300))  # 调整窗口大小
        self.Centre()  # 窗口居中

        self.project_name = project_name
        self.plan_name = plan_name

    def get_values(self):
        return {
            'tester': self.tester.GetValue(),
            'project': self.project_name,
            'workloading': self.workloading.GetValue(),
            'plan_name': self.plan_name
        }

    def on_char(self, event):
        # 仅允许数字输入
        keycode = event.GetKeyCode()
        if chr(keycode).isdigit() or keycode == wx.WXK_BACK:
            event.Skip()  # 允许数字输入和删除键
        else:
            return  # 阻止其他字符输入

class ButtonRenderer(wx.grid.GridCellRenderer):
    """自定义按钮渲染器，仅显示蓝色字体"""

    def __init__(self, label="按钮"):
        super().__init__()
        self.label = label  # 按钮上的文字

    def Draw(self, grid, attr, dc, rect, row, col, isSelected):
        """绘制蓝色字体"""
        # 清除背景
        dc.SetBrush(wx.Brush(wx.Colour(255, 255, 255)))  # 白色背景
        dc.SetPen(wx.TRANSPARENT_PEN)  # 无边框
        dc.DrawRectangle(rect.x, rect.y, rect.width, rect.height)

        # 设置字体颜色为蓝色
        dc.SetTextForeground(wx.Colour(0, 0, 255))  # 蓝色字体
        font = dc.GetFont()
        font.SetWeight(wx.FONTWEIGHT_BOLD)  # 粗体文字
        dc.SetFont(font)

        # 绘制文字
        text_width, text_height = dc.GetTextExtent(self.label)
        text_x = rect.x + (rect.width - text_width) // 2
        text_y = rect.y + (rect.height - text_height) // 2
        dc.DrawText(self.label, text_x, text_y)

    def GetBestSize(self, grid, attr, dc, row, col):
        """返回按钮的最佳尺寸"""
        dc.SetFont(grid.GetFont())
        text_width, text_height = dc.GetTextExtent(self.label)
        # 返回文本的宽度和高度，并添加适当的边距
        return wx.Size(text_width + 10, text_height + 10)

    def Clone(self):
        """克隆渲染器实例"""
        return ButtonRenderer(self.label)


class EditCaseTitleDialog(wx.Dialog):
    def __init__(self, parent, case_list):
        super().__init__(parent, title="批量修改用例标题", size=(700, 500),
                         style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
        self.Centre()
        self.case_list = case_list
        self.edits = []

        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # 使用可滚动窗口
        scroll_win = wx.ScrolledWindow(self, style=wx.VSCROLL)
        scroll_win.SetScrollRate(0, 20)  # 竖直滚动
        grid_sizer = wx.FlexGridSizer(cols=2, hgap=10, vgap=8)
        grid_sizer.Add(wx.StaticText(scroll_win, label="CaseID"), 0, wx.ALIGN_CENTER)
        grid_sizer.Add(wx.StaticText(scroll_win, label="用例标题（可编辑）"), 0, wx.ALIGN_CENTER)

        for case in self.case_list:
            grid_sizer.Add(wx.StaticText(scroll_win, label=str(case['CaseID'])), 0, wx.ALIGN_CENTER_VERTICAL)
            edit = wx.TextCtrl(scroll_win, value=case['CaseTitle'])
            self.edits.append(edit)
            grid_sizer.Add(edit, 1, wx.EXPAND)

        grid_sizer.AddGrowableCol(1, 1)
        scroll_win.SetSizer(grid_sizer)
        scroll_win.FitInside()
        scroll_win.SetMinSize((650, 380))  # 设置内容区最小高度

        main_sizer.Add(scroll_win, 1, wx.ALL | wx.EXPAND, 10)

        # 按钮
        btn_sizer = wx.StdDialogButtonSizer()
        btn_ok = wx.Button(self, wx.ID_OK, label="保存")
        btn_cancel = wx.Button(self, wx.ID_CANCEL, label="取消")
        btn_sizer.AddButton(btn_ok)
        btn_sizer.AddButton(btn_cancel)
        btn_sizer.Realize()
        main_sizer.Add(btn_sizer, 0, wx.ALIGN_CENTER | wx.ALL, 10)

        self.SetSizer(main_sizer)
        self.Layout()
        self.Fit()

    def get_modified_titles(self):
        return [
            {'CaseID': case['CaseID'], 'CaseTitle': edit.GetValue()}
            for case, edit in zip(self.case_list, self.edits)
        ]


class AddUserDialog(wx.Dialog):
    def __init__(self, parent):
        super().__init__(parent, title="添加用户", size=(350, 220))
        self.Centre()

        vbox = wx.BoxSizer(wx.VERTICAL)

        # 用户名
        hbox_user = wx.BoxSizer(wx.HORIZONTAL)
        hbox_user.Add(wx.StaticText(self, label="用户名："), 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 8)
        self.username_ctrl = wx.TextCtrl(self)
        hbox_user.Add(self.username_ctrl, 1, wx.EXPAND)
        vbox.Add(hbox_user, 0, wx.ALL | wx.EXPAND, 10)

        # 密码（默认123456）
        hbox_pwd = wx.BoxSizer(wx.HORIZONTAL)
        hbox_pwd.Add(wx.StaticText(self, label="密码："), 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 8)
        self.password_ctrl = wx.TextCtrl(self, value="123456")
        hbox_pwd.Add(self.password_ctrl, 1, wx.EXPAND)
        vbox.Add(hbox_pwd, 0, wx.ALL | wx.EXPAND, 10)

        # 管理员勾选框
        self.admin_checkbox = wx.CheckBox(self, label="管理员 (admin)")
        vbox.Add(self.admin_checkbox, 0, wx.LEFT | wx.TOP, 18)

        # 按钮
        btn_sizer = wx.StdDialogButtonSizer()
        btn_ok = wx.Button(self, wx.ID_OK, label="添加")
        btn_cancel = wx.Button(self, wx.ID_CANCEL, label="取消")
        btn_sizer.AddButton(btn_ok)
        btn_sizer.AddButton(btn_cancel)
        btn_sizer.Realize()
        vbox.Add(btn_sizer, 0, wx.ALIGN_CENTER | wx.ALL, 10)

        self.SetSizer(vbox)
        self.Layout()
        self.Fit()

    def get_user_info(self):
        return {
            "username": self.username_ctrl.GetValue().strip(),
            "password": self.password_ctrl.GetValue().strip(),
            "is_admin": self.admin_checkbox.GetValue()
        }


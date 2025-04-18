import sys
import os
import pandas as pd
from PyQt5.QtWidgets import (QApplication, QMainWindow, QPushButton, QVBoxLayout, QHBoxLayout,
                             QWidget, QFileDialog, QListWidget, QLabel, QMessageBox, QToolButton,
                             QProgressBar)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QObject


class ExcelProcessorWorker(QObject):
    """Excel处理工作线程"""
    progress_updated = pyqtSignal(int)  # 进度更新信号
    processing_file = pyqtSignal(str)  # 当前处理文件信号
    finished = pyqtSignal(bool, str)  # 完成信号，带成功状态和消息

    def __init__(self, input_files, output_file):
        super().__init__()
        self.input_files = input_files
        self.output_file = output_file

    def process(self):
        try:
            # 初始化结果列表和临时变量
            results = []
            current_level0 = None
            current_level1 = None

            total_files = len(self.input_files)

            # 处理每个文件，保持状态连续
            for file_index, file_path in enumerate(self.input_files):
                self.processing_file.emit(f"正在处理: {os.path.basename(file_path)}")

                # 读取Excel文件
                df = pd.read_excel(file_path)

                # 将列名转换为小写以便于不区分大小写比较
                df.columns = [col.lower() if isinstance(col, str) else col for col in df.columns]

                # 确保level列和Part Number列存在（不区分大小写）
                level_col = next((col for col in df.columns if isinstance(col, str) and col.lower() == 'level'), None)
                part_number_col = next(
                    (col for col in df.columns if isinstance(col, str) and col.lower() == 'part number'), None)

                if level_col is None or part_number_col is None:
                    print(f"警告：文件 {file_path} 缺少必要的列，跳过处理")
                    continue

                # 计算当前文件的行数，用于进度更新
                total_rows = len(df)

                # 遍历数据行
                for i, row in df.iterrows():
                    # 更新进度 - 基于当前文件的进度和总文件数计算
                    progress = int((file_index * 100 + (i / total_rows) * 100) / total_files)
                    self.progress_updated.emit(progress)

                    level = row[level_col]
                    # 移除Part Number中的空格
                    part_number = str(row[part_number_col]).strip()

                    # 排除level=3的数据
                    if level == 3:
                        continue

                    # 找到level 0
                    if level == 0:
                        current_level0 = part_number.replace(" ", "")  # 移除空格
                        current_level1 = None

                    # 找到level 1
                    elif level == 1:
                        current_level1 = part_number.replace(" ", "")  # 移除空格

                    # 处理level 2
                    elif level == 2 and current_level1 is not None:
                        part_number_clean = part_number.replace(" ", "")  # 移除空格

                        # 排除以S86或CTO开头的数据（忽略大小写）
                        if not part_number_clean.upper().startswith(('S86', 'CTO')):
                            # 添加到结果
                            mtm = part_number_clean  # level 2 作为 MTM
                            sbb = current_level1  # level 1 作为 SBB
                            option = current_level0 if current_level0 else ""  # level 0 作为 OPTION
                            mtmsbbopt = f"{mtm}{sbb}{option}"  # 拼接

                            results.append({
                                'MTM': mtm,
                                'SBB': sbb,
                                'OPTION': option,
                                'MTMSBBOPT': mtmsbbopt
                            })

            # 创建结果DataFrame
            result_df = pd.DataFrame(results)

            # 保存到新的Excel文件
            result_df.to_excel(self.output_file, index=False)

            # 完成处理，发送成功信号
            self.progress_updated.emit(100)
            self.finished.emit(True, f"处理完成，结果已保存到 {self.output_file}")

        except Exception as e:
            # 处理过程中出错，发送错误信号
            self.finished.emit(False, f"处理过程中发生错误: {str(e)}")


class ExcelProcessorApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Excel文件处理工具")
        self.setGeometry(100, 100, 800, 600)

        self.file_list = []  # 存储选择的文件路径
        self.thread = None  # 处理线程
        self.worker = None  # 工作对象

        self.init_ui()

    def init_ui(self):
        # 创建主窗口部件和布局
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)

        # 文件选择部分
        file_section = QWidget()
        file_layout = QVBoxLayout(file_section)

        # 添加文件按钮
        self.add_files_btn = QPushButton("添加Excel文件")
        self.add_files_btn.clicked.connect(self.add_files)
        file_layout.addWidget(self.add_files_btn)

        # 文件列表显示
        file_list_label = QLabel("已选择的文件（按处理顺序排列）:")
        file_layout.addWidget(file_list_label)

        self.file_listwidget = QListWidget()
        file_layout.addWidget(self.file_listwidget)

        # 文件排序按钮
        btn_layout = QHBoxLayout()
        self.move_up_btn = QPushButton("上移")
        self.move_up_btn.clicked.connect(self.move_file_up)
        self.move_down_btn = QPushButton("下移")
        self.move_down_btn.clicked.connect(self.move_file_down)
        self.remove_btn = QPushButton("移除")
        self.remove_btn.clicked.connect(self.remove_file)

        btn_layout.addWidget(self.move_up_btn)
        btn_layout.addWidget(self.move_down_btn)
        btn_layout.addWidget(self.remove_btn)

        file_layout.addLayout(btn_layout)

        # 输出文件选择
        output_layout = QHBoxLayout()
        output_layout.addWidget(QLabel("输出文件:"))

        self.output_path_label = QLabel("未选择")
        output_layout.addWidget(self.output_path_label, 1)

        self.select_output_btn = QToolButton()
        self.select_output_btn.setText("...")
        self.select_output_btn.clicked.connect(self.select_output_file)
        output_layout.addWidget(self.select_output_btn)

        file_layout.addLayout(output_layout)

        # 进度条
        self.progress_label = QLabel("准备就绪")
        file_layout.addWidget(self.progress_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        file_layout.addWidget(self.progress_bar)

        # 处理按钮
        self.process_btn = QPushButton("开始处理")
        self.process_btn.clicked.connect(self.process_files)
        file_layout.addWidget(self.process_btn)

        main_layout.addWidget(file_section)

        self.setCentralWidget(main_widget)

    def add_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "选择Excel文件", "", "Excel Files (*.xlsx *.xls)"
        )

        if files:
            for file in files:
                if file not in self.file_list:
                    self.file_list.append(file)
                    self.file_listwidget.addItem(os.path.basename(file))

    def move_file_up(self):
        current_row = self.file_listwidget.currentRow()
        if current_row > 0:
            # 移动列表项
            item = self.file_listwidget.takeItem(current_row)
            self.file_listwidget.insertItem(current_row - 1, item)
            self.file_listwidget.setCurrentRow(current_row - 1)

            # 同步更新文件列表
            file = self.file_list.pop(current_row)
            self.file_list.insert(current_row - 1, file)

    def move_file_down(self):
        current_row = self.file_listwidget.currentRow()
        if current_row < self.file_listwidget.count() - 1 and current_row >= 0:
            # 移动列表项
            item = self.file_listwidget.takeItem(current_row)
            self.file_listwidget.insertItem(current_row + 1, item)
            self.file_listwidget.setCurrentRow(current_row + 1)

            # 同步更新文件列表
            file = self.file_list.pop(current_row)
            self.file_list.insert(current_row + 1, file)

    def remove_file(self):
        current_row = self.file_listwidget.currentRow()
        if current_row >= 0:
            # 移除列表项和文件路径
            self.file_listwidget.takeItem(current_row)
            self.file_list.pop(current_row)

    def select_output_file(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self, "选择输出文件", "", "Excel Files (*.xlsx)"
        )

        if file_path:
            if not file_path.endswith('.xlsx'):
                file_path += '.xlsx'
            self.output_path_label.setText(file_path)

    def process_files(self):
        if not self.file_list:
            QMessageBox.warning(self, "警告", "请先添加Excel文件")
            return

        output_file = self.output_path_label.text()
        if output_file == "未选择":
            QMessageBox.warning(self, "警告", "请选择输出文件")
            return

        # 禁用界面控件，防止多次点击
        self.set_controls_enabled(False)

        # 重置进度条
        self.progress_bar.setValue(0)
        self.progress_label.setText("准备处理...")

        # 创建工作线程
        self.thread = QThread()
        self.worker = ExcelProcessorWorker(self.file_list, output_file)
        self.worker.moveToThread(self.thread)

        # 连接信号
        self.thread.started.connect(self.worker.process)
        self.worker.progress_updated.connect(self.update_progress)
        self.worker.processing_file.connect(self.update_status)
        self.worker.finished.connect(self.process_finished)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

        # 启动线程
        self.thread.start()

    def update_progress(self, value):
        """更新进度条"""
        self.progress_bar.setValue(value)

    def update_status(self, message):
        """更新状态标签"""
        self.progress_label.setText(message)

    def process_finished(self, success, message):
        """处理完成后的回调"""
        # 重新启用界面控件
        self.set_controls_enabled(True)

        # 重置状态和进度条
        self.reset_ui_state()

        if success:
            QMessageBox.information(self, "成功", message)
        else:
            QMessageBox.critical(self, "错误", message)

    def reset_ui_state(self):
        """重置UI状态为初始状态"""
        self.progress_bar.setValue(0)
        self.progress_label.setText("准备就绪")

    def set_controls_enabled(self, enabled):
        """设置界面控件的启用状态"""
        self.add_files_btn.setEnabled(enabled)
        self.move_up_btn.setEnabled(enabled)
        self.move_down_btn.setEnabled(enabled)
        self.remove_btn.setEnabled(enabled)
        self.select_output_btn.setEnabled(enabled)
        self.process_btn.setEnabled(enabled)
        self.file_listwidget.setEnabled(enabled)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ExcelProcessorApp()
    window.show()
    sys.exit(app.exec_())

import re
import sys
import os
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QPushButton, QFileDialog,
    QVBoxLayout, QMessageBox, QHBoxLayout, QTextEdit, QSizePolicy
)
from PyQt5.QtCore import QThread, pyqtSignal, Qt
from PyQt5.QtGui import QFont, QIcon
import pandas as pd
import pymysql

# 数据库连接信息
DB_HOST = "10.196.155.148"
DB_USER = "a_appconnect"
DB_PASSWORD = "dHt6BGB4Zxi^"
DB_DATABASE = "patvs_back"

# 建立数据库连接
conn = pymysql.connect(
    host=DB_HOST,
    user=DB_USER,
    password=DB_PASSWORD,
    database=DB_DATABASE,
    charset='utf8mb4'
)
def safe_filename(name):
    # 去除首尾空格，替换所有非法字符和连续空格
    name = name.strip()
    name = re.sub(r'[\\/:\*\?"<>\|]', '_', name)
    name = re.sub(r'\s+', ' ', name)  # 多个空格合成一个
    return name

class ExportThread(QThread):
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, usernames, export_folder):
        super().__init__()
        self.usernames = usernames
        self.export_folder = export_folder

    def run(self):
        try:
            conn = pymysql.connect(
                host=DB_HOST,
                user=DB_USER,
                password=DB_PASSWORD,
                database=DB_DATABASE,
                charset='utf8mb4'
            )
            for username in self.usernames:
                plan_sql = """
                SELECT t.id as plan_id, t.plan_name, t.project_name
                FROM patvs_back.testplan t
                INNER JOIN patvs_back.users u ON t.userId = u.userId
                WHERE u.username = %s
                """
                plans = pd.read_sql(plan_sql, conn, params=[username])

                if plans.empty:
                    continue

                for _, row in plans.iterrows():
                    plan_id = row['plan_id']
                    plan_name = row['plan_name']
                    project_name = row['project_name']
                    sql = """
                    SELECT 
                        tc.CaseTitle,
                        tc.PreConditions,
                        tc.CaseSteps,
                        tc.ExpectedResult,
                        te.ExecutionID,
                        te.TestResult,
                        te.TestTime,
                        te.StartTime,
                        te.EndTime,
                        te.FailCount,
                        te.BlockCount
                    FROM patvs_back.testexecution te
                    JOIN patvs_back.testcase tc ON te.CaseID = tc.CaseID
                    JOIN patvs_back.testsheet ts ON tc.sheet_id = ts.id
                    WHERE ts.plan_id = %s
                    """
                    df = pd.read_sql(sql, conn, params=[plan_id])
                    # 全部做安全处理
                    safe_project_name = safe_filename(str(project_name))
                    safe_plan_name = safe_filename(str(plan_name))
                    folder_name = os.path.join(self.export_folder, f"{username}-{safe_project_name}")
                    os.makedirs(folder_name, exist_ok=True)
                    file_path = os.path.join(folder_name, f"{safe_plan_name}.xlsx")
                    df = pd.read_sql(sql, conn, params=[plan_id])
                    df.to_excel(file_path, index=False, engine='openpyxl')
            conn.close()
            self.finished.emit('全部导出完成！')
        except Exception as e:
            self.error.emit(str(e))

class Exporter(QWidget):
    def __init__(self):
        super().__init__()
        self.export_folder = ""
        self.export_thread = None
        self.initUI()

    def initUI(self):
        self.setWindowTitle('测试计划数据导出工具')
        self.setWindowIcon(QIcon()) # 可自行添加ico

        font_label = QFont('微软雅黑', 13)
        font_input = QFont('微软雅黑', 13)
        font_btn = QFont('微软雅黑', 13, QFont.Bold)
        font_path = QFont('微软雅黑', 11)

        main_layout = QVBoxLayout()
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(40, 35, 40, 35)

        # 标题
        label_title = QLabel('测试计划数据导出工具')
        label_title.setFont(QFont('微软雅黑', 18, QFont.Bold))
        label_title.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(label_title)

        # 用户名输入
        label_user = QLabel('请输入用户名（多个用英文逗号分隔）：')
        label_user.setFont(font_label)
        self.input_user = QLineEdit()
        self.input_user.setFont(font_input)
        self.input_user.setPlaceholderText('如：zhangsan,lisi,wangwu')
        self.input_user.setMinimumHeight(36)
        main_layout.addWidget(label_user)
        main_layout.addWidget(self.input_user)

        # 文件夹选择
        folder_layout = QHBoxLayout()
        self.btn_select_folder = QPushButton('选择导出文件夹')
        self.btn_select_folder.setFont(font_btn)
        self.btn_select_folder.setStyleSheet(
            "QPushButton {background-color: #4CAF50; color: white; border-radius: 5px; padding: 6px 18px;}"
            "QPushButton:hover {background-color: #45a049;}"
        )
        self.btn_select_folder.clicked.connect(self.choose_folder)

        self.label_folder = QTextEdit('未选择文件夹')
        self.label_folder.setFont(font_path)
        self.label_folder.setReadOnly(True)
        self.label_folder.setMaximumHeight(38)
        self.label_folder.setMinimumHeight(38)
        self.label_folder.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.label_folder.setStyleSheet("background: #f5f5f5; border: 1px solid #aaa; border-radius: 4px;")
        folder_layout.addWidget(self.btn_select_folder)
        folder_layout.addWidget(self.label_folder)
        main_layout.addLayout(folder_layout)

        # 导出按钮
        self.btn_export = QPushButton('开始导出')
        self.btn_export.setFont(font_btn)
        self.btn_export.setMinimumHeight(40)
        self.btn_export.setStyleSheet(
            "QPushButton {background-color: #2196F3; color: white; border-radius: 6px; padding: 8px 30px; font-size:16px;}"
            "QPushButton:hover {background-color: #1976D2;}"
        )
        self.btn_export.clicked.connect(self.start_export)
        main_layout.addWidget(self.btn_export, alignment=Qt.AlignCenter)

        # 底部提示
        label_tip = QLabel('温馨提示：\n1. 支持多个用户名，英文逗号分隔。\n2. 导出过程请耐心等待。')
        label_tip.setFont(QFont('微软雅黑', 10))
        label_tip.setStyleSheet("color: #777;")
        main_layout.addWidget(label_tip)

        self.setLayout(main_layout)
        self.resize(620, 410)

    def choose_folder(self):
        folder = QFileDialog.getExistingDirectory(self, '选择导出文件夹')
        if folder:
            self.export_folder = folder
            self.label_folder.setText(folder)

    def start_export(self):
        usernames = [u.strip() for u in self.input_user.text().split(',') if u.strip()]
        if not usernames:
            QMessageBox.warning(self, '提示', '请输入至少一个用户名。')
            return
        if not self.export_folder:
            QMessageBox.warning(self, '提示', '请选择导出文件夹。')
            return
        self.btn_export.setEnabled(False)
        self.btn_export.setText("正在导出，请稍候...")
        self.export_thread = ExportThread(usernames, self.export_folder)
        self.export_thread.finished.connect(self.on_export_finished)
        self.export_thread.error.connect(self.on_export_error)
        self.export_thread.start()

    def on_export_finished(self, msg):
        self.btn_export.setEnabled(True)
        self.btn_export.setText('开始导出')
        QMessageBox.information(self, '完成', msg)

    def on_export_error(self, err):
        self.btn_export.setEnabled(True)
        self.btn_export.setText('开始导出')
        QMessageBox.critical(self, '错误', f'导出失败：{err}')

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = Exporter()
    ex.show()
    sys.exit(app.exec_())
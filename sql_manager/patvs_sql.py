# -*- coding: utf-8 -*-
# 负责存储逻辑
import sqlite3
from datetime import datetime
from common.logs import logger
from common.tools import Public
import os
import sys
import math


class Patvs_SQL():
    def __init__(self):
        self.conn = sqlite3.connect(r"D:\PATVS\sqlite-tools\lenovoDb")

    def update_start_time_by_case_id(self, case_id, actions, actions_num):
        cur = self.conn.cursor()
        try:
            cur.execute("SELECT StartTime,TestResult FROM TestCase WHERE caseID = ?", (case_id,))
            result = cur.fetchall()
            logger.info(result)
            if result and result[0][0] is not None and result[0][1] is None:  # 确保result的查询结果不是None并且 StartTime（result[0]）也位置None
                logger.info(f"已有执行记录时间 {result},仅修改监控动作和次数")
                cur.execute("UPDATE TestCase SET Actions = ?, ActionsNum = ? WHERE CaseID = ?",
                            (actions, actions_num, case_id))
            else:
                now = datetime.now()
                formatted_now = now.strftime('%Y-%m-%d %H:%M:%S')
                logger.info("开始记录执行时间，动作和次数")
                cur.execute("UPDATE TestCase SET StartTime = ?, Actions = ?, ActionsNum = ? WHERE CaseID = ?",
                            (formatted_now, actions, actions_num, case_id))
        except Exception as e:
            logger.error(f"An error occurred: {e}")
            self.conn.rollback()
        else:
            self.conn.commit()
        finally:
            cur.close()

    def update_end_time_case_id(self, case_id, case_result, comment=None):
        cur = self.conn.cursor()
        try:
            cur.execute(f'SELECT StartTime FROM TestCase where CaseID = ?', (case_id,))
            result = cur.fetchone()
            execution_time = datetime.strptime(result[0], "%Y-%m-%d %H:%M:%S")
            now = datetime.now()
            test_time = int((now - execution_time).total_seconds())
            logger.info(f"测试消耗时间是 {test_time}")
            formatted_now = now.strftime('%Y-%m-%d %H:%M:%S')
            comment = comment or None  # 如果comment为空，则将其设为None
            cur.execute(
                "UPDATE TestCase SET EndTime = ?, TestTime = ?, TestResult = ?, comment = ? WHERE CaseID = ?",
                (formatted_now, test_time, case_result, comment, case_id))
        except Exception as e:
            logger.error(f"An error occurred: {e}")
            self.conn.rollback()
        else:
            self.conn.commit()
        finally:
            cur.close()

    def insert_case_by_filename(self, file_name, tester, case_data):
        cur = self.conn.cursor()
        try:
            logger.info(f"start inserting {file_name} into DB ")
            cur.execute("INSERT INTO TestFile (FileName, Tester) VALUES (?, ?)", (file_name, tester))
            # 获取刚刚插入的 TestFile 记录的 FileID
            file_id = cur.lastrowid
            for case in case_data:
                cur.execute(
                    "INSERT INTO TestCase (ModelName, CaseTitle, CaseSteps, ExpectedResult, FileID) VALUES (?, ?, ?, ?, ?)",
                    (case[0], case[1], case[2], case[3], file_id))
        except Exception as e:
            logger.error(f"An error occurred: {e}")
            self.conn.rollback()
        else:
            self.conn.commit()
        finally:
            cur.close()

    def select_case_by_filename(self, filename):
        cur = self.conn.cursor()
        cur.execute(f'SELECT FileID FROM TestFile where Filename = ?', (filename,))
        result = cur.fetchone()
        if result:
            file_id = result[0]
        else:
            file_id = 1
        cur.execute(f'SELECT * FROM TestCase where FileID = ?', (file_id,))
        all_case = cur.fetchall()
        return all_case

    def select_filename_by_name(self, file_name):
        cur = self.conn.cursor()
        cur.execute("SELECT FileName FROM TestFile WHERE FileName=?", (file_name,))
        result = cur.fetchone()
        cur.close()
        if result:
            return True
        else:
            return False

    def select_all_filename_by_tester(self, tester):
        cur = self.conn.cursor()
        cur.execute("SELECT FileName FROM TestFile WHERE Tester=?", (tester,))
        result = cur.fetchall()
        cur.close()
        logger.info(result)
        if result:
            return [res[0] for res in result]
        else:
            return None

    def select_all_tester(self):
        cur = self.conn.cursor()
        cur.execute("SELECT Tester FROM TestFile")
        result = cur.fetchall()
        cur.close()
        logger.info(result)
        if result:
            return list({res[0] for res in result})
        else:
            return None

    def select_fileid_by_file_name(self, file_name):
        cur = self.conn.cursor()
        cur.execute("SELECT FileID FROM TestFile WHERE FileName=?", (file_name,))
        result = cur.fetchone()
        logger.info(f'fileID is {result}')
        if result:
            return result[0]
        else:
            return None

    def select_cases_by_case_id(self, case_id):
        cur = self.conn.cursor()
        cur.execute("SELECT FileID FROM TestCase WHERE CaseID=?", (case_id,))
        result = cur.fetchone()
        file_id = result[0] if result else None
        logger.info(f'FileID is {file_id}')
        if file_id:
            cur.execute("SELECT * FROM TestCase WHERE FileID=?", (file_id,))
            all_cases = cur.fetchall()
            return all_cases
        else:
            return None

    def update_test_num_by_id(self, test_num, case_id):
        """
        更新测试次数
        """
        cur = self.conn.cursor()
        try:
            cur.execute("UPDATE TestCase SET TestNum = ? WHERE CaseID = ?", (test_num, case_id))
        except Exception as e:
            logger.error(f"An error occurred: {e}")
            self.conn.rollback()
        else:
            self.conn.commit()
        finally:
            cur.close()

    def select_test_num_by_id(self, case_id):
        cur = self.conn.cursor()
        cur.execute('SELECT TestNum FROM TestCase WHERE CaseID = ?', (case_id,))
        result = cur.fetchone()
        cur.close()
        if result:
            return result[0]
        else:
            return None

    def reset_case_by_case_id(self, case_id):
        """
        重置用例状态
        """
        cur = self.conn.cursor()
        try:
            cur.execute("""
                UPDATE TestCase 
                SET EndTime = NULL, 
                    TestTime = NULL, 
                    TestResult = NULL, 
                    comment = NULL, 
                    StartTime = NULL, 
                    Actions = NULL, 
                    ActionsNum = NULL, 
                    TestNum = NULL
                WHERE CaseID = ?
            """, (case_id,))
        except Exception as e:
            logger.error(f"An error occurred: {e}")
            self.conn.rollback()
        else:
            self.conn.commit()
        finally:
            cur.close()

    def count_case_by_filename(self, filename):
        """
        统计用例总数
        :param filename: 测试文件的名称
        :return: 返回该测试文件中的用例总数
        """
        cur = self.conn.cursor()
        try:
            cur.execute("SELECT FileID FROM TestFile WHERE FileName=?", (filename,))
            file_id_result = cur.fetchone()
            if file_id_result:
                file_id = file_id_result[0]
                cur.execute("SELECT COUNT(*) FROM TestCase WHERE FileID=?", (file_id,))
                count_result = cur.fetchone()
                return count_result[0] if count_result else 0
            else:
                logger.error(f"No entries found for filename: {filename}")
                return 0
        except sqlite3.Error as e:
            logger.error(f"An error occurred: {e.args[0]}")
            return 0
        finally:
            cur.close()

    def count_case_time_by_filename(self, filename):
        """
        统计总用例耗时
        :param filename: 测试文件的名称
        :return: 返回该测试文件中的总用例耗时
        """
        cur = self.conn.cursor()
        try:
            cur.execute("SELECT FileID FROM TestFile WHERE FileName=?", (filename,))
            file_id_result = cur.fetchone()
            if file_id_result:
                file_id = file_id_result[0]
                cur.execute("SELECT SUM(TestTime) FROM TestCase WHERE FileID=?", (file_id,))
                count_result = cur.fetchone()
                if count_result and count_result[0] is not None:
                    # 使用math.ceil函数将秒转换为分钟，并向上取整
                    total_time_in_min = math.ceil(count_result[0] / 60.0)
                    return str(total_time_in_min) + ' min'
                else:
                    return 0
            else:
                logger.error(f"No entries found for filename: {filename}")
                return 0
        except sqlite3.Error as e:
            logger.error(f"An error occurred: {e.args[0]}")
            return 0
        finally:
            cur.close()

    def count_executed_case_by_filename(self, filename):
        """
        统计已执行用例数
        :param filename: 测试文件的名称
        :return: 返回该测试文件中已执行的用例数
        """
        cur = self.conn.cursor()
        try:
            cur.execute("SELECT FileID FROM TestFile WHERE FileName = ?", (filename,))
            result = cur.fetchone()
            if result:
                file_id = result[0]
                # 统计已执行的用例数量
                cur.execute("SELECT COUNT(*) FROM TestCase WHERE FileID = ? AND TestResult IS NOT NULL", (file_id,))
                executed_count = cur.fetchone()[0]
                return executed_count
            else:
                logger.error(f"No test file found with the name: {filename}")
                return 0
        except Exception as e:
            logger.error(f"An error occurred: {e}")
            return 0
        finally:
            cur.close()

    def count_pass_rate_by_filename(self, filename):
        """
        统计通过用例
        :param filename: 测试文件的名称
        :return: 返回该测试文件中已通过的用例数
        """
        cur = self.conn.cursor()
        try:
            cur.execute("SELECT FileID FROM TestFile WHERE FileName = ?", (filename,))
            result = cur.fetchone()
            if result:
                file_id = result[0]
                cur.execute("SELECT COUNT(*) FROM TestCase WHERE FileID = ? AND TestResult = 'Pass'", (file_id,))
                pass_count = cur.fetchone()[0]
                return pass_count
            else:
                logger.error(f"No test file found with the name: {filename}")
                return 0
        except Exception as e:
            logger.error(f"An error occurred: {e}")
            return 0
        finally:
            cur.close()

    def calculate_progress_and_pass_rate(self, filename):
        """
        计算测试用例的执行进度和通过率
        :return: 返回包含执行进度和通过率的字典
        """
        # 项目耗时
        case_time_count = self.count_case_time_by_filename(filename)
        # 总用例数
        case_count = self.count_case_by_filename(filename)
        # 已执行用例数
        executed_cases_count = self.count_executed_case_by_filename(filename)
        # 通过用例数
        pass_count = self.count_pass_rate_by_filename(filename)
        # 初始化执行进度和通过率
        execution_progress = "0.00%"
        pass_rate = "0.00%"
        if case_count > 0:
            # 计算执行进度百分比
            execution_progress = (executed_cases_count / case_count) * 100
            execution_progress = f"{execution_progress:.2f}%"
            # 计算通过率百分比
            pass_rate = (pass_count / case_count) * 100
            pass_rate = f"{pass_rate:.2f}%"
        return {
            "case_count": case_count,
            "executed_cases_count": executed_cases_count,
            "execution_progress": execution_progress,
            "pass_rate": pass_rate,
            "case_time_count": case_time_count
        }

    def select_start_time(self, case_id):
        cur = self.conn.cursor()
        try:
            cur.execute("SELECT StartTime FROM TestCase WHERE CaseID = ?", (case_id,))
            result = cur.fetchone()
            logger.info(result)
            if result[0] is None:
                # 查询结果为空，获取当前时间
                current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                cur.execute("UPDATE TestCase SET StartTime = ? WHERE CaseID = ?", (current_time, case_id))
                self.conn.commit()
                # 返回当前时间
                return current_time
            else:
                # 查询结果不为空，返回查询得到的时间
                return result[0]
        except Exception as e:
            logger.error(f"Error selecting or updating start time for CaseID {case_id}: {e}")
            self.conn.rollback()
        finally:
            cur.close()


if __name__ == '__main__':
    data = Patvs_SQL()
    file = data.select_start_time(22)
    print(file)

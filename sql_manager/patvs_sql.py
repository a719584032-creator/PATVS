# -*- coding: utf-8 -*-
# 负责存储逻辑
import mysql.connector
from datetime import datetime
from common.logs import logger
from common.tools import Public
import os
import sys
import math
from werkzeug.security import generate_password_hash, check_password_hash


class Patvs_SQL():
    def __init__(self):
        self.conn = mysql.connector.connect(
            host="rm-cn-lf63r60vh0003gto.rwlb.rds.aliyuncs.com",
            user="yesq3_lenovo",
            password="patvs_Lenovo",
            database="lenovoDb",
            buffered=True
        )

    def update_start_time_by_case_id(self, case_id, actions, actions_num):
        cur = self.conn.cursor()
        try:
            cur.execute("SELECT StartTime,TestResult FROM TestCase WHERE caseID = %s", (case_id,))
            result = cur.fetchall()
            logger.info(result)
            # 确保result的查询结果不是None并且 StartTime（result[0]）也位置None
            if result and result[0][0] is not None and result[0][1] is None:
                logger.info(f"已有执行记录时间 {result},仅修改监控动作和次数")
                cur.execute("UPDATE TestCase SET Actions = %s, TestNum = %s WHERE CaseID = %s",
                            (actions, actions_num, case_id))
            else:
                now = datetime.now()
                formatted_now = now.strftime('%Y-%m-%d %H:%M:%S')
                logger.info("开始记录执行时间，动作和次数")
                cur.execute("UPDATE TestCase SET StartTime = %s, Actions = %s, TestNum = %s WHERE CaseID = %s",
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
            cur.execute(f'SELECT StartTime FROM TestCase where CaseID = %s', (case_id,))
            result = cur.fetchone()
            # logger.info(result)
            # logger.info(type(result))
            # execution_time = datetime.strptime(result[0], "%Y-%m-%d %H:%M:%S")
            now = datetime.now()
            test_time = int((now - result[0]).total_seconds())
            logger.info(f"测试消耗时间是 {test_time}")
            formatted_now = now.strftime('%Y-%m-%d %H:%M:%S')
            comment = comment or None  # 如果comment为空，则将其设为None
            cur.execute(
                "UPDATE TestCase SET EndTime = %s, TestTime = %s, TestResult = %s, comment = %s WHERE CaseID = %s",
                (formatted_now, test_time, case_result, comment, case_id))
        except Exception as e:
            logger.error(f"An error occurred: {e}")
            self.conn.rollback()
        else:
            self.conn.commit()
        finally:
            cur.close()

    def insert_case_by_filename(self, plan_name, project_name, sheet_name, tester, workloading, filename, cases, model_name):
        cursor = self.conn.cursor()
        filename = os.path.basename(filename)  # 获取文件名
        try:
            # 查询是否已经存在相同的 plan_name
            cursor.execute("SELECT id FROM TestPlan WHERE plan_name = %s", (plan_name,))
            result = cursor.fetchone()

            if result:
                # 已经存在相同的 plan_name，获取其 id
                plan_id = result[0]
            else:
                # 插入新的 TestPlan 记录
                plan_query = """
                        INSERT INTO TestPlan (plan_name, filename)
                        VALUES (%s, %s)
                    """
                cursor.execute(plan_query, (plan_name, filename))
                plan_id = cursor.lastrowid

            # 检查是否已经存在相同的 sheet_name
            cursor.execute("SELECT id FROM TestSheet WHERE sheet_name = %s AND plan_id = %s", (sheet_name, plan_id))
            sheet_result = cursor.fetchone()

            if sheet_result:
                logger.warning(
                    f"Sheet '{sheet_name}' already exists for plan '{plan_name}', skipping insertion of sheet and cases.")
                return  # 如果 sheet_name 已经存在，直接跳过后续操作
            else:
                # 插入新的 TestSheet 记录
                sheet_query = """
                        INSERT INTO TestSheet (sheet_name, project_name, tester, workloading, plan_id)
                        VALUES (%s, %s, %s, %s, %s)
                    """
                cursor.execute(sheet_query, (sheet_name, project_name, tester, workloading, plan_id))
                sheet_id = cursor.lastrowid

                # 插入到 TestCase 表
                case_query = """
                        INSERT INTO TestCase (ModelName, CaseTitle, CaseSteps, ExpectedResult, sheet_id)
                        VALUES (%s, %s, %s, %s, %s)
                    """
                for case in cases:
                    for model in model_name:
                        cursor.execute(case_query, (model, case['title'], case['steps'], case['expected'], sheet_id))

            # 提交事务
            self.conn.commit()
        except BaseException as err:
            logger.error(f"Error: {err}")
            self.conn.rollback()
            raise f"Error: {err}"
        finally:
            cursor.close()

    def select_case_by_sheet_id(self, sheet_id):
        cur = self.conn.cursor()
        query = """
        SELECT * FROM TestCase WHERE sheet_id = %s
        """
        cur.execute(query, (sheet_id,))
        all_case = cur.fetchall()
        cur.close()
        return all_case

    def select_all_plan_names_by_username(self, username):
        cur = self.conn.cursor()
        query = """
        SELECT DISTINCT tp.plan_name
        FROM TestPlan tp
        JOIN TestSheet ts ON tp.id = ts.plan_id
        WHERE ts.tester = %s
        """
        cur.execute(query, (username,))
        result = cur.fetchall()
        cur.close()
        logger.info(result)
        if result:
            # 返回所有 plan_name 的列表
            return [res[0] for res in result]
        else:
            return []

    def select_all_sheet_names_by_plan_and_username(self, plan_name, username):
        cur = self.conn.cursor()
        query = """
        SELECT ts.id, ts.sheet_name
        FROM TestSheet ts
        JOIN TestPlan tp ON ts.plan_id = tp.id
        WHERE tp.plan_name = %s AND ts.tester = %s
        """
        cur.execute(query, (plan_name, username))
        result = cur.fetchall()
        cur.close()
        logger.info(result)
        if result:
            # 返回所有 sheet_name 的列表
            return result
        else:
            return []

    def select_userid_by_username(self, username):
        cur = self.conn.cursor()
        cur.execute("SELECT userId FROM users WHERE userId=%s", (username,))
        result = cur.fetchall()
        cur.close()
        logger.info(result)
        if result:
            return result[0]
        else:
            return None

    def select_filename_by_filename(self, filename):
        cur = self.conn.cursor()
        cur.execute("SELECT filename FROM TestPlan WHERE filename=%s", (filename,))
        result = cur.fetchone()
        logger.info(f'filename is {result}')
        if result:
            return result[0]
        else:
            return False

    def select_plan_name_by_filename(self, filename):
        cur = self.conn.cursor()
        cur.execute("SELECT plan_name FROM TestPlan WHERE filename=%s", (filename,))
        result = cur.fetchone()
        logger.info(f'plan_name is {result}')
        if result:
            return result[0]
        else:
            return False

    def select_cases_by_case_id(self, case_id):
        cur = self.conn.cursor()
        cur.execute("SELECT sheet_id FROM TestCase WHERE CaseID=%s", (case_id,))
        result = cur.fetchone()
        file_id = result[0] if result else None
        logger.info(f'sheet_id is {file_id}')
        if file_id:
            cur.execute("SELECT * FROM TestCase WHERE sheet_id=%s", (file_id,))
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
            cur.execute("UPDATE TestCase SET TestNum = %s WHERE CaseID = %s", (test_num, case_id))
        except Exception as e:
            logger.error(f"An error occurred: {e}")
            self.conn.rollback()
        else:
            self.conn.commit()
        finally:
            cur.close()

    def select_test_num_by_id(self, case_id):
        cur = self.conn.cursor()
        cur.execute('SELECT TestNum FROM TestCase WHERE CaseID = %s', (case_id,))
        result = cur.fetchone()
        cur.close()
        if result:
            return result[0]
        else:
            return None

    def select_case_result_by_id(self, case_id):
        """
        获取测试结果
        """
        cur = self.conn.cursor()
        cur.execute('SELECT TestResult FROM TestCase WHERE CaseID = %s', (case_id,))
        result = cur.fetchone()
        cur.close()
        return result if result[0] is not None else False

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
                    TestNum = NULL
                WHERE CaseID = %s
            """, (case_id,))
        except Exception as e:
            logger.error(f"An error occurred: {e}")
            self.conn.rollback()
        else:
            self.conn.commit()
        finally:
            cur.close()

    def count_case_by_sheet_id(self, sheet_id):
        """
        统计用例总数
        :param sheet_id: 测试sheet页的名称
        :return: 返回该测试文件中的用例总数
        """
        cur = self.conn.cursor()
        try:
            cur.execute("SELECT COUNT(*) FROM TestCase WHERE sheet_id=%s", (sheet_id,))
            count_result = cur.fetchone()
            return count_result[0] if count_result else 0
        except mysql.connector.Error as e:
            logger.error(f"An error occurred: {e.args[0]}")
            return 0
        finally:
            cur.close()

    def count_case_time_by_sheet_id(self, sheet_id):
        """
        统计总用例耗时
        :param sheet_id: 测试文件的sheet_id
        :return: 返回该测试文件中的总用例耗时
        """
        cur = self.conn.cursor()
        try:
            cur.execute("SELECT SUM(TestTime) FROM TestCase WHERE sheet_id=%s", (sheet_id,))
            count_result = cur.fetchone()
            if count_result and count_result[0] is not None:
                # 使用math.ceil函数将秒转换为分钟，并向上取整
                total_time_in_min = math.ceil(count_result[0] / 60.0)
                return str(total_time_in_min) + ' min'
            else:
                return 0
        except mysql.connector.Error as e:
            logger.error(f"An error occurred: {e.args[0]}")
            return 0
        finally:
            cur.close()

    def count_executed_case_by_sheet_id(self, sheet_id):
        """
        统计已执行用例数
        :param sheet_name: 测试文件的名称
        :return: 返回该测试文件中已执行的用例数
        """
        cur = self.conn.cursor()
        try:
            # 统计已执行的用例数量
            cur.execute("SELECT COUNT(*) FROM TestCase WHERE sheet_id = %s AND TestResult IS NOT NULL", (sheet_id,))
            executed_count = cur.fetchone()
            return executed_count[0] if executed_count else 0
        except Exception as e:
            logger.error(f"An error occurred: {e}")
            return 0
        finally:
            cur.close()

    def count_pass_rate_by_sheet_id(self, sheet_id):
        """
        统计通过用例
        :param sheet_name: 测试文件的名称
        :return: 返回该测试文件中已通过的用例数
        """
        cur = self.conn.cursor()
        try:
            cur.execute("SELECT COUNT(*) FROM TestCase WHERE sheet_id = %s AND TestResult = 'Pass'", (sheet_id,))
            pass_count = cur.fetchone()
            return pass_count[0] if pass_count else 0
        except Exception as e:
            logger.error(f"An error occurred: {e}")
            return 0
        finally:
            cur.close()

    def calculate_progress_and_pass_rate(self, sheet_id):
        """
        计算测试用例的执行进度和通过率
        :return: 返回包含执行进度和通过率的字典
        """
        logger.info('111111111111111111111111')
        # 项目耗时
        case_time_count = self.count_case_time_by_sheet_id(sheet_id)
        # 总用例数
        case_count = self.count_case_by_sheet_id(sheet_id)
        # 已执行用例数
        executed_cases_count = self.count_executed_case_by_sheet_id(sheet_id)
        # 通过用例数
        pass_count = self.count_pass_rate_by_sheet_id(sheet_id)
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
        logger.warning({
            "case_count": case_count,
            "executed_cases_count": executed_cases_count,
            "execution_progress": execution_progress,
            "pass_rate": pass_rate,
            "case_time_count": case_time_count
        })
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
            cur.execute("SELECT StartTime FROM TestCase WHERE CaseID = %s", (case_id,))
            result = cur.fetchone()
            logger.info(result)
            if result[0] is None:
                # 查询结果为空，获取当前时间
                current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                cur.execute("UPDATE TestCase SET StartTime = %s WHERE CaseID = %s", (current_time, case_id))
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

    def add_user(self, username, password):
        password_hash = generate_password_hash(password)
        cur = self.conn.cursor()

        cur.execute('INSERT INTO users (username, password_hash) VALUES (%s, %s)',
                    (username, password_hash))
        self.conn.commit()

    def validate_user(self, username, password):
        cur = self.conn.cursor()
        cur.execute('SELECT * FROM users WHERE username = %s', (username,))
        user = cur.fetchone()
        logger.info(user)
        if user and check_password_hash(user[2], password):
            return True, user[4]
        return False, None

    def change_user_password(self, username, old_password, new_password):
        cur = self.conn.cursor()
        cur.execute('SELECT * FROM users WHERE username = %s', (username,))
        user = cur.fetchone()
        if user and check_password_hash(user[2], old_password):
            new_password_hash = generate_password_hash(new_password)
            cur.execute('UPDATE users SET password_hash = %s WHERE username = %s',
                        (new_password_hash, username))
            self.conn.commit()
            return True
        return False

    def sell_all(self):
        cur = self.conn.cursor()
        cur.execute('SELECT * FROM TestCase')
        user = cur.fetchall()
        logger.info(user)

if __name__ == '__main__':
    data = Patvs_SQL()
    #  data.add_user('yesq3', '123456')
    # data.validate_user('zhangjq9', '123456')
    # res = data.select_plan_name_by_filename('D:\PATVS\TestPlanWithResult_K510_Keyboard_K510_Audit_test_20240411173441.xlsx')
    # if res:
    #     print(res)
    res = data.select_case_result_by_id(2481)
    if res:
        print(res)
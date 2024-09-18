# -*- coding: utf-8 -*-
# testcase sql 管理
import mysql.connector
from datetime import datetime
from common.logs import logger
import os
import math
from werkzeug.security import generate_password_hash, check_password_hash
import re


class TestCaseManager:
    def __init__(self, connection, cursor):
        self.conn = connection
        self.cursor = cursor

    def update_start_time_by_case_id(self, case_id, actions):
        self.cursor.execute("SELECT StartTime,TestResult FROM TestCase WHERE caseID = %s", (case_id,))
        result = self.cursor.fetchall()
        logger.info(result)
        # 确保result的查询结果不是None并且 StartTime（result[0]）也位置None
        if result and result[0][0] is not None and result[0][1] is None:
            logger.info(f"已有执行记录时间 {result},仅修改监控动作和次数")
            self.cursor.execute("UPDATE TestCase SET Actions = %s WHERE CaseID = %s",
                                (actions, case_id))
        else:
            now = datetime.now()
            formatted_now = now.strftime('%Y-%m-%d %H:%M:%S')
            logger.info("开始记录执行时间，动作和次数")
            logger.warning(formatted_now)
            self.cursor.execute("UPDATE TestCase SET StartTime = %s, Actions = %s WHERE CaseID = %s",
                                (formatted_now, actions, case_id))

    def update_end_time_case_id(self, case_id, case_result, comment=None):
        self.cursor.execute(f'SELECT StartTime FROM TestCase where CaseID = %s', (case_id,))
        result = self.cursor.fetchone()

        now = datetime.now()
        test_time = int((now - result[0]).total_seconds())
        logger.info(f"测试消耗时间是 {test_time}")
        formatted_now = now.strftime('%Y-%m-%d %H:%M:%S')
        # 更新测试结果
        self.cursor.execute(
            "UPDATE TestCase SET EndTime = %s, TestTime = %s, TestResult = %s WHERE CaseID = %s",
            (formatted_now, test_time, case_result, case_id)
        )
        # 插入评论
        if comment:
            logger.warning("开始插入评论................................")
            self.cursor.execute(
                "INSERT INTO TestCaseComments (CaseID, Comment, CommentTime) VALUES (%s, %s, %s)",
                (case_id, comment, formatted_now)
            )
            logger.warning("插入结束................................")

    def select_comments_for_case(self, case_id):
        self.cursor.execute(
            "SELECT Comment, CommentTime FROM TestCaseComments WHERE CaseID = %s ORDER BY CommentTime ASC",
            (case_id,)
        )
        comments = self.cursor.fetchall()
        formatted_comments = "\n".join(f"{comment_time}: {comment}" for comment, comment_time in comments)
        return formatted_comments

    def select_all_comments(self, case_ids):
        # Fetch all comments for the provided list of case IDs
        format_strings = ','.join(['%s'] * len(case_ids))
        self.cursor.execute(
            f"SELECT CaseID, Comment, CommentTime FROM TestCaseComments WHERE CaseID IN ({format_strings}) ORDER BY CommentTime ASC",
            tuple(case_ids)
        )
        comments_data = self.cursor.fetchall()

        # Organize comments by CaseID
        comments_map = {}
        for case_id, comment, comment_time in comments_data:
            if case_id not in comments_map:
                comments_map[case_id] = []
            comments_map[case_id].append(f"{comment_time}: {comment}")

        # Convert lists of comments to concatenated strings
        for case_id in comments_map:
            comments_map[case_id] = "\n".join(comments_map[case_id])

        return comments_map

    def insert_case_by_filename(self, plan_name, project_name, sheet_name, tester, workloading, filename, cases,
                                model_name):
        filename = os.path.basename(filename)  # 获取文件名
        try:
            # 查询是否已经存在相同的 plan_name
            self.cursor.execute("SELECT id FROM TestPlan WHERE plan_name = %s", (plan_name,))
            result = self.cursor.fetchone()

            if result:
                # 已经存在相同的 plan_name，获取其 id
                plan_id = result[0]
            else:
                # 插入新的 TestPlan 记录
                plan_query = "INSERT INTO TestPlan (plan_name, filename) VALUES (%s, %s)"
                self.cursor.execute(plan_query, (plan_name, filename))
                plan_id = self.cursor.lastrowid

            # 检查是否已经存在相同的 sheet_name
            self.cursor.execute("SELECT id FROM TestSheet WHERE sheet_name = %s AND plan_id = %s",
                                (sheet_name, plan_id))
            sheet_result = self.cursor.fetchone()

            if sheet_result:
                # 如果 sheet_name 已经存在，直接跳过后续操作
                logger.warning(f"Sheet '{sheet_name}' already exists for plan '{plan_name}', skipping insertion.")
                return
            else:
                # 插入新的 TestSheet 记录
                sheet_query = "INSERT INTO TestSheet (sheet_name, project_name, tester, workloading, plan_id) VALUES (%s, %s, %s, %s, %s)"
                self.cursor.execute(sheet_query, (sheet_name, project_name, tester, workloading, plan_id))
                sheet_id = self.cursor.lastrowid

                # 插入到 TestCase 表
                case_query = "INSERT INTO TestCase (ModelName, CaseTitle, CaseSteps, ExpectedResult, sheet_id) VALUES (%s, %s, %s, %s, %s)"
                for case in cases:
                    for model in model_name:
                        self.cursor.execute(case_query,
                                            (model, case['title'], case['steps'], case['expected'], sheet_id))
        except Exception as err:
            logger.error(f"Error: {err}")
            raise Exception(f"Error: {err}")

    def insert_case_by_power_filename(self, filename, sheet_name, project_name, tester, workloading, cases):
        plan_name = os.path.basename(filename)  # 获取文件名
        try:
            # 查询是否已经存在相同的 plan_name
            self.cursor.execute("SELECT id FROM TestPlan WHERE plan_name = %s", (plan_name,))
            result = self.cursor.fetchone()

            if result:
                # 已经存在相同的 plan_name，获取其 id
                plan_id = result[0]
            else:
                # 插入新的 TestPlan 记录
                plan_query = "INSERT INTO TestPlan (plan_name, filename) VALUES (%s, %s)"
                self.cursor.execute(plan_query, (plan_name, filename))
                plan_id = self.cursor.lastrowid

            # 检查是否已经存在相同的 sheet_name
            self.cursor.execute("SELECT id FROM TestSheet WHERE sheet_name = %s AND plan_id = %s",
                                (sheet_name, plan_id))
            sheet_result = self.cursor.fetchone()

            if sheet_result:
                # 如果 sheet_name 已经存在，直接跳过后续操作
                logger.warning(f"Sheet '{sheet_name}' already exists for plan '{plan_name}', skipping insertion.")
                return
            else:
                # 插入新的 TestSheet 记录
                sheet_query = "INSERT INTO TestSheet (sheet_name, project_name, tester, workloading, plan_id) VALUES (%s, %s, %s, %s, %s)"
                self.cursor.execute(sheet_query, (sheet_name, project_name, tester, workloading, plan_id))
                sheet_id = self.cursor.lastrowid

                # 插入到 TestCase 表
                case_query = "INSERT INTO TestCase (ModelName, CaseTitle, PreConditions, CaseSteps, ExpectedResult, sheet_id) VALUES (%s, %s, %s, %s, %s, %s)"
                for case in cases:
                    self.cursor.execute(case_query,
                                        (case['model_name'], case['title'], case['preconditions'], case['steps'], case['expected'], sheet_id))
        except Exception as err:
            logger.error(f"Error: {err}")
            raise Exception(f"Error: {err}")

    def select_case_by_sheet_id(self, sheet_id):
        query = "SELECT * FROM TestCase WHERE sheet_id = %s"
        self.cursor.execute(query, (sheet_id,))
        all_case = self.cursor.fetchall()
        return all_case

    def select_all_plan_names_by_username(self, username):
        query = """
        SELECT DISTINCT tp.plan_name
        FROM TestPlan tp
        JOIN TestSheet ts ON tp.id = ts.plan_id
        WHERE ts.tester = %s
        """
        self.cursor.execute(query, (username,))
        result = self.cursor.fetchall()
        logger.info(result)
        return [plan_name[0] for plan_name in result]

    def select_all_plan_names(self):
        query = "SELECT plan_name FROM TestPlan "
        self.cursor.execute(query, )
        result = self.cursor.fetchall()
        logger.info(result)
        return [plan_name[0] for plan_name in result]

    def select_all_sheet_names_by_plan_and_username(self, plan_name, username):
        query = """
        SELECT ts.id, ts.sheet_name
        FROM TestSheet ts
        JOIN TestPlan tp ON ts.plan_id = tp.id
        WHERE tp.plan_name = %s AND ts.tester = %s
        """
        self.cursor.execute(query, (plan_name, username))
        result = self.cursor.fetchall()
        logger.info(result)
        if result:
            # 返回id和sheet_names
            return result
        else:
            return []

    def select_all_sheet_names_by_plan(self, plan_name):
        query = """
        SELECT ts.id, ts.sheet_name
        FROM TestSheet ts
        JOIN TestPlan tp ON ts.plan_id = tp.id
        WHERE tp.plan_name = %s
        """
        self.cursor.execute(query, (plan_name,))
        result = self.cursor.fetchall()
        logger.info(result)
        if result:
            # 返回id和sheet_names
            return result
        else:
            return []

    def select_userid_by_username(self, username):
        query = "SELECT id FROM User WHERE username = %s"
        self.cursor.execute(query, (username,))
        result = self.cursor.fetchone()
        logger.info(result)
        return result[0] if result else None

    def select_filename_by_filename(self, filename):
        query = "SELECT filename FROM TestPlan WHERE filename = %s"
        self.cursor.execute(query, (filename,))
        result = self.cursor.fetchone()
        logger.info(result)
        return result[0] if result else None

    def select_plan_name_by_filename(self, filename):
        query = "SELECT plan_name FROM TestPlan WHERE filename = %s"
        self.cursor.execute(query, (filename,))
        result = self.cursor.fetchone()
        logger.info(result)
        return result[0] if result else None

    def select_plan_name_by_plan_name(self, plan_name):
        query = "SELECT plan_name FROM TestPlan WHERE plan_name = %s"
        self.cursor.execute(query, (plan_name,))
        result = self.cursor.fetchone()
        logger.info(result)
        return result[0] if result else None

    def select_cases_by_case_id(self, case_id):
        self.cursor.execute("SELECT sheet_id FROM TestCase WHERE CaseID=%s", (case_id,))
        result = self.cursor.fetchone()
        file_id = result[0] if result else None
        logger.info(f'sheet_id is {file_id}')
        if file_id:
            self.cursor.execute("SELECT * FROM TestCase WHERE sheet_id=%s", (file_id,))
            all_cases = self.cursor.fetchall()
            return all_cases
        else:
            return None

    def update_test_num_by_id(self, test_num, case_id):
        query = "UPDATE TestCase SET test_num = %s WHERE id = %s"
        self.cursor.execute(query, (test_num, case_id))

    def select_test_num_by_id(self, case_id):
        self.cursor.execute('SELECT TestNum FROM TestCase WHERE CaseID = %s', (case_id,))
        result = self.cursor.fetchone()
        if result:
            return result[0]
        else:
            return None

    def select_case_result_by_id(self, case_id):
        """
        获取测试结果
        """
        self.cursor.execute('SELECT TestResult FROM TestCase WHERE CaseID = %s', (case_id,))
        result = self.cursor.fetchone()
        return result if result[0] is not None else False

    def reset_case_by_case_id(self, case_id):
        """
        重置用例状态
        """
        self.cursor.execute("""
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

    def count_case_by_sheet_id(self, sheet_id):
        """
        统计用例总数
        :param sheet_id: 测试sheet页的名称
        :return: 返回该测试文件中的用例总数
        """
        try:
            self.cursor.execute("SELECT COUNT(*) FROM TestCase WHERE sheet_id=%s", (sheet_id,))
            count_result = self.cursor.fetchone()
            return count_result[0] if count_result else 0
        except mysql.connector.Error as e:
            logger.error(f"An error occurred: {e.args[0]}")
            return 0

    def count_workloading_by_sheet_id(self, sheet_id):
        """
        统计理论用例耗时
        :param sheet_id: 测试文件的sheet_id
        :return: 返回该测试文件中的总用例理论耗时
        """
        try:
            self.cursor.execute("SELECT workloading FROM TestSheet WHERE id=%s", (sheet_id,))
            workloading_result = self.cursor.fetchone()
            if workloading_result and workloading_result[0] is not None:
                # 提取数字部分并转换为分钟
                match = re.search(r'\d+', workloading_result[0])
                if match:
                    return int(match.group(0))
                else:
                    return 0
            else:
                return 0
        except mysql.connector.Error as e:
            logger.error(f"An error occurred: {e.args[0]}")
            return 0

    def count_case_time_by_sheet_id(self, sheet_id):
        """
        统计总用例耗时
        :param sheet_id: 测试文件的sheet_id
        :return: 返回该测试文件中的总用例耗时
        """
        try:
            self.cursor.execute("SELECT SUM(TestTime) FROM TestCase WHERE sheet_id=%s", (sheet_id,))
            count_result = self.cursor.fetchone()
            if count_result and count_result[0] is not None:
                # 使用math.ceil函数将秒转换为分钟，并向上取整
                total_time_in_min = math.ceil(count_result[0] / 60.0)
                return total_time_in_min
            else:
                return 0
        except mysql.connector.Error as e:
            logger.error(f"An error occurred: {e.args[0]}")
            return 0

    def count_executed_case_by_sheet_id(self, sheet_id):
        """
        统计已执行用例数
        :param sheet_id: 测试文件的sheet_id
        :return: 返回该测试文件中已执行的用例数
        """
        try:
            # 统计已执行的用例数量
            self.cursor.execute("SELECT COUNT(*) FROM TestCase WHERE sheet_id = %s AND TestResult IS NOT NULL",
                                (sheet_id,))
            executed_count = self.cursor.fetchone()
            return executed_count[0] if executed_count else 0
        except Exception as e:
            logger.error(f"An error occurred: {e}")
            return 0

    def count_test_case_results_by_sheet_id(self, sheet_id):
        """
        统计通过、失败和阻塞的用例
        :param sheet_id: 测试文件的sheet_id
        :return: 返回该测试文件中已通过、失败和阻塞的用例数
        """
        try:
            query = """
            SELECT 
                SUM(CASE WHEN TestResult = 'Pass' THEN 1 ELSE 0 END) AS pass_count,
                SUM(CASE WHEN TestResult = 'Fail' THEN 1 ELSE 0 END) AS fail_count,
                SUM(CASE WHEN TestResult = 'Block' THEN 1 ELSE 0 END) AS block_count
            FROM TestCase 
            WHERE sheet_id = %s
            """
            self.cursor.execute(query, (sheet_id,))
            result = self.cursor.fetchone()
            pass_count, fail_count, block_count = result if result else (0, 0, 0)
            return {
                'pass_count': pass_count,
                'fail_count': fail_count,
                'block_count': block_count
            }
        except Exception as e:
            logger.error(f"An error occurred: {e}")
            return {
                'pass_count': 0,
                'fail_count': 0,
                'block_count': 0
            }

    def calculate_progress_and_pass_rate(self, sheet_id):
        """
        计算测试用例的执行进度和通过率
        :return: 返回包含执行进度和通过率的字典
        """
        # 项目耗时
        case_time_count = self.count_case_time_by_sheet_id(sheet_id)
        # 理论耗时
        workloading_time = self.count_workloading_by_sheet_id(sheet_id)
        # 总用例数
        case_count = self.count_case_by_sheet_id(sheet_id)
        # 已执行用例数
        executed_cases_count = self.count_executed_case_by_sheet_id(sheet_id)
        # 通过用例数
        result_count = self.count_test_case_results_by_sheet_id(sheet_id)

        # 计算执行进度百分比
        def calculate_percentage(part, whole):
            return f"{(part / whole) * 100:.2f}%" if whole > 0 else "0.00%"

        execution_progress = calculate_percentage(executed_cases_count, case_count)
        pass_rate = calculate_percentage(result_count['pass_count'], case_count)
        fail_rate = calculate_percentage(result_count['fail_count'], case_count)
        block_rate = calculate_percentage(result_count['block_count'], case_count)

        logger.warning({
            "case_count": case_count,
            "executed_cases_count": executed_cases_count,
            "execution_progress": execution_progress,
            "pass_rate": pass_rate,
            "fail_rate": fail_rate,
            "block_rate": block_rate,
            "pass_count": result_count['pass_count'],
            "fail_count": result_count['fail_count'],
            "block_count": result_count['block_count'],
            "case_time_count": case_time_count,
            "workloading_time": workloading_time
        })
        return {
            "case_count": case_count,
            "executed_cases_count": executed_cases_count,
            "execution_progress": execution_progress,
            "pass_rate": pass_rate,
            "fail_rate": fail_rate,
            "block_rate": block_rate,
            "pass_count": result_count['pass_count'],
            "fail_count": result_count['fail_count'],
            "block_count": result_count['block_count'],
            "case_time_count": case_time_count,
            "workloading_time": workloading_time
        }

    def count_case_time_by_plan_id(self, plan_id):
        """
        统计总用例耗时
        :param plan_id: 测试计划的plan_id
        :return: 返回该测试计划中的总用例耗时
        """
        try:
            self.cursor.execute(
                "SELECT SUM(TestTime) FROM TestCase WHERE sheet_id IN (SELECT id FROM TestSheet WHERE plan_id=%s)",
                (plan_id,))
            count_result = self.cursor.fetchone()
            if count_result and count_result[0] is not None:
                total_time_in_min = math.ceil(count_result[0] / 60.0)
                return total_time_in_min
            else:
                return 0
        except mysql.connector.Error as e:
            logger.error(f"An error occurred: {e.args[0]}")
            return 0

    def count_workloading_by_plan_id(self, plan_id):
        """
        统计理论用例耗时
        :param plan_id: 测试计划的plan_id
        :return: 返回该测试计划中的总用例理论耗时
        """
        try:
            self.cursor.execute(
                "SELECT SUM(CAST(SUBSTRING(workloading, 1, LENGTH(workloading) - 4) AS UNSIGNED)) FROM TestSheet WHERE plan_id=%s",
                (plan_id,))
            workloading_result = self.cursor.fetchone()
            if workloading_result and workloading_result[0] is not None:
                total_workloading = workloading_result[0]
                return int(total_workloading)
            else:
                return 0
        except mysql.connector.Error as e:
            logger.error(f"An error occurred: {e.args[0]}")
            return 0

    def count_case_by_plan_id(self, plan_id):
        """
        统计总用例数
        :param plan_id: 测试计划的plan_id
        :return: 返回该测试计划中的总用例数
        """
        try:
            self.cursor.execute(
                "SELECT COUNT(*) FROM TestCase WHERE sheet_id IN (SELECT id FROM TestSheet WHERE plan_id=%s)",
                (plan_id,))
            case_count = self.cursor.fetchone()
            return case_count[0] if case_count else 0
        except Exception as e:
            logger.error(f"An error occurred: {e}")
            return 0

    def count_executed_case_by_plan_id(self, plan_id):
        """
        统计已执行用例数
        :param plan_id: 测试计划的plan_id
        :return: 返回该测试计划中已执行的用例数
        """
        try:
            self.cursor.execute(
                "SELECT COUNT(*) FROM TestCase WHERE sheet_id IN (SELECT id FROM TestSheet WHERE plan_id=%s) AND TestResult IS NOT NULL",
                (plan_id,))
            executed_count = self.cursor.fetchone()
            return executed_count[0] if executed_count else 0
        except Exception as e:
            logger.error(f"An error occurred: {e}")
            return 0

    def count_test_case_results_by_plan_id(self, plan_id):
        """
        统计通过、失败和阻塞的用例
        :param plan_id: 测试计划的plan_id
        :return: 返回该测试计划中已通过、失败和阻塞的用例数
        """
        try:
            query = """
            SELECT 
                SUM(CASE WHEN TestResult = 'Pass' THEN 1 ELSE 0 END) AS pass_count,
                SUM(CASE WHEN TestResult = 'Fail' THEN 1 ELSE 0 END) AS fail_count,
                SUM(CASE WHEN TestResult = 'Block' THEN 1 ELSE 0 END) AS block_count
            FROM TestCase 
            WHERE sheet_id IN (SELECT id FROM TestSheet WHERE plan_id = %s)
            """
            self.cursor.execute(query, (plan_id,))
            result = self.cursor.fetchone()
            pass_count, fail_count, block_count = result if result else (0, 0, 0)
            return {
                'pass_count': pass_count,
                'fail_count': fail_count,
                'block_count': block_count
            }
        except Exception as e:
            logger.error(f"An error occurred: {e}")
            return {
                'pass_count': 0,
                'fail_count': 0,
                'block_count': 0
            }

    def calculate_plan_statistics(self, plan_id):
        """
        计算测试计划的执行进度和通过率
        :return: 返回包含执行进度和通过率的字典
        """
        case_time_count = self.count_case_time_by_plan_id(plan_id)
        workloading_time = self.count_workloading_by_plan_id(plan_id)
        case_count = self.count_case_by_plan_id(plan_id)
        executed_cases_count = self.count_executed_case_by_plan_id(plan_id)
        result_count = self.count_test_case_results_by_plan_id(plan_id)

        # 计算执行进度百分比
        def calculate_percentage(part, whole):
            return f"{(part / whole) * 100:.2f}%" if whole > 0 else "0.00%"

        execution_progress = calculate_percentage(executed_cases_count, case_count)
        pass_rate = calculate_percentage(result_count['pass_count'], case_count)
        fail_rate = calculate_percentage(result_count['fail_count'], case_count)
        block_rate = calculate_percentage(result_count['block_count'], case_count)

        logger.warning({
            "case_count": case_count,
            "executed_cases_count": executed_cases_count,
            "execution_progress": execution_progress,
            "pass_rate": pass_rate,
            "fail_rate": fail_rate,
            "block_rate": block_rate,
            "pass_count": result_count['pass_count'],
            "fail_count": result_count['fail_count'],
            "block_count": result_count['block_count'],
            "case_time_count": case_time_count,
            "workloading_time": workloading_time
        })
        return {
            "case_count": case_count,
            "executed_cases_count": executed_cases_count,
            "execution_progress": execution_progress,
            "pass_rate": pass_rate,
            "fail_rate": fail_rate,
            "block_rate": block_rate,
            "pass_count": result_count['pass_count'],
            "fail_count": result_count['fail_count'],
            "block_count": result_count['block_count'],
            "case_time_count": case_time_count,
            "workloading_time": workloading_time
        }

    def select_start_time(self, case_id):
        self.cursor.execute("SELECT StartTime FROM TestCase WHERE CaseID = %s", (case_id,))
        result = self.cursor.fetchone()
        return result[0]
        # if result[0] is None:
        #     # 查询结果为空，获取当前时间
        #     current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        #     self.cursor.execute("UPDATE TestCase SET StartTime = %s WHERE CaseID = %s", (current_time, case_id))
        #     logger.warning(111111111111111111111111111)
        #     logger.warning(current_time)
        #     # 返回当前时间
        #     return current_time
        # else:
        #     # 查询结果不为空，返回查询得到的时间

    def select_tester_by_plan_or_sheet(self, plan, sheet=None):
        if sheet:
            query = "SELECT DISTINCT tester FROM TestSheet WHERE id = %s"
            self.cursor.execute(query, (sheet,))
        else:
            query = """
            SELECT DISTINCT ts.tester
            FROM TestSheet ts
            JOIN TestPlan tp ON ts.plan_id = tp.id
            WHERE tp.plan_name = %s
            """
            self.cursor.execute(query, (plan,))
        result = self.cursor.fetchall()
        logger.info(result)
        return [tester[0] for tester in result]

    def select_plan_id(self, plan):
        self.cursor.execute('SELECT id FROM TestPlan WHERE plan_name = %s', (plan,))
        plan_id = self.cursor.fetchone()
        logger.info(plan_id)
        return plan_id[0]

    def add_user(self, username, password, role=None):
        password_hash = generate_password_hash(password)
        self.cursor.execute(
            'INSERT INTO users (username, password_hash, role) VALUES (%s, %s, %s)',
            (username, password_hash, role))

    def validate_user(self, username, password):
        self.cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
        user = self.cursor.fetchone()
        logger.info(user)
        if user and check_password_hash(user[2], password):
            return True, user[4]
        return False, None

    def change_user_password(self, username, old_password, new_password):
        self.cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
        user = self.cursor.fetchone()
        if user and check_password_hash(user[2], old_password):
            new_password_hash = generate_password_hash(new_password)
            self.cursor.execute('UPDATE users SET password_hash = %s WHERE username = %s',
                                (new_password_hash, username))
            self.conn.commit()
            return True
        return False

    def sell_all(self):
        cur = self.conn.cursor()
        cur.execute('SELECT * FROM TestCase')
        user = cur.fetchall()
        logger.info(user)

    def select_case_title(self, case_id):
        self.cursor.execute('SELECT CaseTitle FROM TestCase WHERE CaseID = %s', (case_id,))
        case_title = self.cursor.fetchone()
        logger.info(case_title)
        return case_title[0]

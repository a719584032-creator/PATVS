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

    def update_start_time_by_case_id(self, case_id, model_id, start_time):
        # 查询是否存在与 CaseID 和 ModelID 对应的 ExecutionID
        self.cursor.execute(
            """
            SELECT ExecutionID FROM testexecution 
            WHERE CaseID = %s AND ModelID = %s
            """,
            (case_id, model_id)
        )
        result = self.cursor.fetchone()

        if result:
            # 如果存在 ExecutionID，则更新记录
            execution_id = result[0]
            self.cursor.execute(
                """
                UPDATE testexecution 
                SET StartTime = %s 
                WHERE ExecutionID = %s
                """,
                (start_time, execution_id)
            )
            logger.info(f"更新成功，ExecutionID: {execution_id}")
        else:
            # 如果不存在 ExecutionID，则插入新记录
            self.cursor.execute(
                """
                INSERT INTO testexecution (StartTime, CaseID, ModelID) 
                VALUES (%s, %s, %s)
                """,
                (start_time, case_id, model_id)
            )
            logger.info("插入成功")

    def update_end_time_case_id(self, case_id, model_id, case_result, comment=None):
        # 查询执行记录
        result = self.select_start_time(model_id, case_id)
        if result is None:
            raise logger.error("未找到匹配的测试执行记录")

        # 获取ExecutionID
        self.cursor.execute(
            "SELECT ExecutionID FROM testexecution WHERE CaseID = %s AND ModelID = %s",
            (case_id, model_id)
        )
        execution_id = self.cursor.fetchone()
        if execution_id is None:
            raise logger.error("无法获取执行的 ExecutionID")

        # 计算测试耗时
        now = datetime.now()
        test_time = int((now - result).total_seconds())
        logger.info(f"测试消耗时间是 {test_time}")
        formatted_now = now.strftime('%Y-%m-%d %H:%M:%S')

        # 开始事务
        self.cursor.execute("BEGIN")
        # 更新测试结果
        self.cursor.execute(
            "UPDATE testexecution SET EndTime = %s, TestTime = %s, TestResult = %s WHERE ExecutionID = %s",
            (formatted_now, test_time, case_result, execution_id[0])
        )
        # 插入评论
        if comment:
            logger.warning("开始插入评论................................")
            self.cursor.execute(
                "INSERT INTO TestCaseComments (ExecutionID, Comment, CommentTime) VALUES (%s, %s, %s)",
                (execution_id[0], comment, formatted_now)
            )
            # 重新计算 FailCount
            self.cursor.execute(
                "SELECT Comment FROM TestCaseComments WHERE ExecutionID = %s",
                (execution_id[0],)
            )
            comments = [row[0] for row in self.cursor.fetchall()]
            fail_count = sum(c.count('Fail') for c in comments)
            block_count = sum(c.count('Block') for c in comments)

            # 更新 FailCount 字段
            self.cursor.execute(
                "UPDATE testexecution SET FailCount = %s, BlockCount = %s WHERE ExecutionID = %s",
                (fail_count, block_count, execution_id[0])
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

    def select_all_comments(self, execution_ids):
        # Fetch all comments for the provided list of case IDs
        format_strings = ','.join(['%s'] * len(execution_ids))
        self.cursor.execute(
            f"SELECT ExecutionID, Comment, CommentTime FROM TestCaseComments WHERE ExecutionID IN ({format_strings}) ORDER BY CommentTime ASC",
            tuple(execution_ids)
        )
        comments_data = self.cursor.fetchall()

        # Organize comments by ExecutionID
        comments_map = {}
        for execution_id, comment, comment_time in comments_data:
            if execution_id not in comments_map:
                comments_map[execution_id] = []
            comments_map[execution_id].append(f"{comment_time}: {comment}")

        # Convert lists of comments to concatenated strings
        for execution_id in comments_map:
            comments_map[execution_id] = "\n".join(comments_map[execution_id])

        return comments_map

    def insert_case_by_filename(self, plan_name, project_name, project_phase, sheet_name, userid, workloading, filename,
                                cases, model_names):
        filename = os.path.basename(filename)  # 获取文件名
        try:
            # 查询是否已经存在相同的 plan_name
            self.cursor.execute("SELECT id FROM TestPlan WHERE plan_name = %s AND userid = %s", (plan_name, userid))
            result = self.cursor.fetchone()

            if result:
                # 已经存在相同的 plan_name，获取其 id
                plan_id = result[0]
            else:
                # 插入新的 TestPlan 记录
                plan_query = "INSERT INTO TestPlan (plan_name, filename, project_name, project_phase, userid) VALUES (%s, %s, %s, %s, %s)"
                self.cursor.execute(plan_query, (plan_name, filename, project_name, project_phase, userid))
                logger.warning(" 插入 testplan 表成功")
                plan_id = self.cursor.lastrowid

            # 插入到 Model 表并建立与 TestPlan 的关联
            for model_name in model_names:
                # 检查 Model 表中是否已经存在该 model_name
                self.cursor.execute("SELECT ModelID FROM Model WHERE ModelName = %s", (model_name,))
                model_result = self.cursor.fetchone()

                if model_result:
                    # 如果存在，获取其 ModelID
                    model_id = model_result[0]
                else:
                    # 如果不存在，插入新的 Model 记录
                    model_query = "INSERT INTO Model (ModelName) VALUES (%s)"
                    self.cursor.execute(model_query, (model_name,))
                    model_id = self.cursor.lastrowid
                    logger.warning(" 插入 Model 表成功")

                # 检查 TestPlanModel 表中是否已经存在该 PlanID 和 ModelID 的组合
                self.cursor.execute("SELECT 1 FROM TestPlanModel WHERE PlanID = %s AND ModelID = %s",
                                    (plan_id, model_id))
                if not self.cursor.fetchone():
                    # 如果组合不存在，则插入新的关联记录
                    self.cursor.execute("INSERT INTO TestPlanModel (PlanID, ModelID) VALUES (%s, %s)",
                                        (plan_id, model_id))

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
                sheet_query = "INSERT INTO TestSheet (sheet_name, tester, workloading, plan_id) VALUES (%s, %s, %s, %s)"
                self.cursor.execute(sheet_query, (sheet_name, userid, workloading, plan_id))
                sheet_id = self.cursor.lastrowid

                # 插入到 TestCase 表
                case_query = "INSERT INTO TestCase (CaseTitle, CaseSteps, ExpectedResult, sheet_id) VALUES (%s, %s, %s, %s)"
                for case in cases:
                    self.cursor.execute(case_query,
                                        (case['title'], case['steps'], case['expected'], sheet_id))
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
                logger.warning(f"plan_name: {plan_name} 已存在，skipping insertion")
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
                                        (case['model_name'], case['title'], case['preconditions'], case['steps'],
                                         case['expected'], sheet_id))
        except Exception as err:
            logger.error(f"Error: {err}")
            raise Exception(f"Error: {err}")

    def select_case_by_sheet_id(self, sheet_id):
        query = "SELECT * FROM TestCase WHERE sheet_id = %s"
        self.cursor.execute(query, (sheet_id,))
        all_case = self.cursor.fetchall()
        return all_case

    def select_all_project_names_by_username(self, userid):
        """
        根据用户身份返回项目列表：
        - 如果用户是管理员 (role = admin)，则返回所有项目。
        - 如果用户不是管理员，则根据 userId 返回对应的项目。
        """
        # 查询用户角色
        role_query = "SELECT role FROM users WHERE userId = %s"
        self.cursor.execute(role_query, (userid,))
        role_result = self.cursor.fetchone()
        # 如果用户是管理员，查询所有项目
        if role_result and role_result[0] == 'admin':
            logger.info(f"用户ID {userid} 的角色为 {role_result[0]}")
            query = "SELECT DISTINCT project_name FROM TestPlan"
            self.cursor.execute(query)
        else:
            # 如果用户不是管理员，根据 userId 查询项目
            query = "SELECT DISTINCT project_name FROM TestPlan WHERE userId = %s"
            self.cursor.execute(query, (userid,))

        # 获取查询结果
        result = self.cursor.fetchall()
        # 返回项目名称列表
        return [project_name[0] for project_name in result]

    def select_all_plan_names_by_project(self, userid, project_name):
        """
        根据用户身份返回计划列表：
        - 如果用户是管理员 (role = admin)，则返回指定项目下的所有计划。
        - 如果用户不是管理员，则根据 userId 和项目名称返回对应的计划。
        """

        # 查询用户角色
        role_query = "SELECT role FROM users WHERE userId = %s"
        self.cursor.execute(role_query, (userid,))
        role_result = self.cursor.fetchone()

        # 如果用户是管理员，查询指定项目下的所有计划
        if role_result and role_result[0] == 'admin':
            logger.info(f"用户ID {userid} 的角色为 {role_result[0]}")
            query = """
            SELECT id, plan_name FROM TestPlan WHERE project_name = %s
            """
            self.cursor.execute(query, (project_name,))
        else:
            # 如果用户不是管理员，根据 userId 和项目名称查询计划
            query = """
            SELECT id, plan_name FROM TestPlan WHERE userId = %s AND project_name = %s
            """
            self.cursor.execute(query, (userid, project_name))

        # 获取查询结果
        result = self.cursor.fetchall()

        # 返回id和plan_names
        return result if result else []

    def select_all_model_names_by_plan_id(self, plan_id):
        query = """
            SELECT m.ModelID, m.ModelName
            FROM model m
            JOIN testplanmodel tpm ON m.ModelID = tpm.ModelID
            WHERE tpm.PlanID = %s
        """
        self.cursor.execute(query, (plan_id,))
        result = self.cursor.fetchall()
        logger.info(result)
        # 返回 ModelID 和 ModelName 列表
        return result if result else []

    def select_all_sheet_names_by_plan_id(self, plan_id):
        query = """
        SELECT id, sheet_name FROM TestSheet where plan_id = %s
        """
        self.cursor.execute(query, (plan_id,))
        result = self.cursor.fetchall()
        logger.info(result)
        # 返回id和sheet_names
        return result if result else []

    def select_case_status(self, model_id, sheet_id):
        query = """
        SELECT   
            te.TestResult,
            te.TestTime,
            te.StartTime,
            te.EndTime,
            GROUP_CONCAT(CONCAT(IFNULL(tcc.CommentTime, 'N/A'), ': ', IFNULL(tcc.Comment, 'No Comment')) ORDER BY tcc.CommentTime ASC SEPARATOR '\n') AS Comments,
            tc.CaseTitle,
            tc.PreConditions,
            tc.CaseSteps,
            tc.ExpectedResult,
            te.ExecutionID,
            te.ModelID,
            tc.CaseID,
            tc.sheet_id,
            te.FailCount,
            te.BlockCount
        FROM testcase tc
        LEFT JOIN testexecution te ON te.CaseID = tc.CaseID AND te.ModelID = %s
        LEFT JOIN TestCaseComments tcc ON tcc.ExecutionID = te.ExecutionID
        WHERE tc.sheet_id = %s
        GROUP BY tc.CaseID, tc.sheet_id
        """

        self.cursor.execute(query, (model_id, sheet_id))
        result = self.cursor.fetchall()
        logger.info(result)
        return result

    def select_all_plan_names(self):
        query = "SELECT plan_name FROM TestPlan "
        self.cursor.execute(query, )
        result = self.cursor.fetchall()
        logger.info(result)
        return [plan_name[0] for plan_name in result]

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
        query = "SELECT userId FROM users WHERE username = %s"
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

    def select_plan_name_by_plan_name(self, plan_name, user_id):
        query = "SELECT plan_name FROM TestPlan WHERE plan_name = %s AND userId = %s"
        self.cursor.execute(query, (plan_name, user_id))
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

    def select_case_result_by_id(self, case_id, model_id):
        """
        获取测试结果
        """
        self.cursor.execute(
            'SELECT TestResult FROM testexecution WHERE CaseID = %s AND ModelID = %s',
            (case_id, model_id)
        )
        result = self.cursor.fetchone()

        if result:
            logger.info(f"查询成功，TestResult: {result[0]}")
            return result[0]  # 返回具体的 TestResult 值
        else:
            logger.info("未找到匹配的测试结果")
            return None

    def select_case_result_by_execution_id(self, execution_id):
        self.cursor.execute(
            'SELECT TestResult FROM testexecution WHERE ExecutionID = %s ', (execution_id,)
        )
        result = self.cursor.fetchone()

        if result:
            logger.info(f"查询成功，TestResult: {result[0]}")
            return result[0]  # 返回具体的 TestResult 值
        else:
            logger.info("未找到匹配的测试结果")
            return None

    def reset_case_by_execution_id(self, execution_id):
        """
        重置用例状态
        """
        self.cursor.execute("""
            UPDATE testexecution 
            SET EndTime = NULL, 
                TestTime = NULL, 
                TestResult = NULL, 
                StartTime = NULL
            WHERE ExecutionID = %s
        """, (execution_id,))

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

    def count_case_time_by_sheet_id(self, model_id, sheet_id):
        """
        统计总用例耗时
        :param sheet_id: 测试文件的sheet_id
        :return: 返回该测试文件中的总用例耗时
        """
        try:
            query = """
            SELECT SUM(te.TestTime) FROM testexecution te JOIN TestCase tc 
            ON te.CaseID = tc.CaseID 
            WHERE tc.sheet_id=%s AND te.ModelID = %s
            """
            self.cursor.execute(query, (model_id, sheet_id))
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

    def count_executed_case_by_sheet_id(self, model_id, sheet_id):
        """
        统计已执行用例数
        :param sheet_id: 测试文件的sheet_id
        :return: 返回该测试文件中已执行的用例数
        """
        query = """
        SELECT COUNT(*) FROM testexecution te JOIN TestCase tc 
        ON te.CaseID = tc.CaseID
        WHERE tc.sheet_id = %s AND te.ModelID = %s AND te.TestResult IS NOT NULL
        """
        try:
            # 统计已执行的用例数量
            self.cursor.execute(query, (model_id, sheet_id))
            executed_count = self.cursor.fetchone()
            return executed_count[0] if executed_count else 0
        except Exception as e:
            logger.error(f"An error occurred: {e}")
            return 0

    def count_test_case_results_by_sheet_id(self, model_id, sheet_id):
        """
        统计通过、失败和阻塞的用例
        :param model_id: 模型ID
        :param sheet_id: 测试文件的sheet_id
        :return: 返回该测试文件中已通过、失败和阻塞的用例数
        """
        try:
            query = """
                    SELECT 
                        SUM(CASE WHEN te.TestResult = 'Pass' THEN 1 ELSE 0 END) AS pass_count,
                        SUM(CASE WHEN te.TestResult = 'Fail' THEN 1 ELSE 0 END) AS fail_count,
                        SUM(CASE WHEN te.TestResult = 'Block' THEN 1 ELSE 0 END) AS block_count
                    FROM testexecution te 
                    JOIN TestCase tc ON te.CaseID = tc.CaseID 
                    WHERE tc.sheet_id = %s AND te.ModelID = %s
            """
            # 注意参数顺序
            self.cursor.execute(query, (sheet_id, model_id))
            result = self.cursor.fetchone()

            # 确保在结果为空时返回0
            if result is None:
                return {
                    'pass_count': 0,
                    'fail_count': 0,
                    'block_count': 0
                }

            pass_count, fail_count, block_count = result
            return {
                'pass_count': pass_count if pass_count is not None else 0,
                'fail_count': fail_count if fail_count is not None else 0,
                'block_count': block_count if block_count is not None else 0
            }
        except Exception as e:
            logger.error(f"An error occurred: {e}")
            return {
                'pass_count': 0,
                'fail_count': 0,
                'block_count': 0
            }

    def calculate_progress_and_pass_rate(self, plan_id, model_id, sheet_id):
        """
        计算测试用例的执行进度和通过率
        :return: 返回包含执行进度和通过率的字典
        """
        # 项目耗时
        case_time_count = self.count_case_time_by_sheet_id(model_id, sheet_id)
        # 理论耗时
        workloading_time = self.count_workloading_by_sheet_id(sheet_id)
        # 总用例数
        case_count = self.count_case_by_sheet_id(sheet_id)
        # 已执行用例数
        executed_cases_count = self.count_executed_case_by_sheet_id(model_id, sheet_id)
        # 通过用例数
        result_count = self.count_test_case_results_by_sheet_id(model_id, sheet_id)
        # 测试环境
        test_phase = self.select_test_phase(plan_id)
        # 测试人员
        tester = self.select_tester_by_plan_or_sheet(plan_id=plan_id)
        logger.warning(case_time_count)
        logger.warning(workloading_time)
        logger.warning(case_count)
        logger.warning(executed_cases_count)
        logger.warning(result_count)

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
            "workloading_time": workloading_time,
            "project_phase": test_phase,
            "tester": tester
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
            "workloading_time": workloading_time,
            "project_phase": test_phase,
            "tester": tester
        }

    def count_case_time_by_plan_id(self, plan_id):
        """
        统计总用例耗时
        :param plan_id: 测试计划的 plan_id
        :return: 返回该测试计划中的总用例耗时（单位：分钟，向上取整）
        """
        try:
            # 查询总耗时，关联 TestExecution 表、TestCase 表 和 TestSheet 表
            query = """
            SELECT SUM(te.TestTime)
            FROM TestExecution te
            INNER JOIN TestCase tc ON te.CaseID = tc.CaseID
            INNER JOIN TestSheet ts ON tc.sheet_id = ts.id
            WHERE ts.plan_id = %s
            """
            self.cursor.execute(query, (plan_id,))
            count_result = self.cursor.fetchone()

            # 如果查询结果存在且不为空，计算总耗时（向上取整，以分钟为单位）
            if count_result and count_result[0] is not None:
                total_time_in_min = math.ceil(count_result[0] / 60.0)
                return total_time_in_min
            else:
                # 如果查询结果为空或耗时为 None，返回 0
                return 0
        except mysql.connector.Error as e:
            # 捕获数据库错误，记录日志并返回 0
            logger.error(f"查询总用例耗时时发生错误: {e.args[0]}")
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
        统计总用例数（考虑关联的机型数量）
        :param plan_id: 测试计划的 plan_id
        :return: 返回该测试计划中的总用例数（用例数 * 关联的机型数）
        """
        try:
            # 查询 plan_id 关联的机型数量
            self.cursor.execute(
                """
                SELECT COUNT(DISTINCT ModelID) 
                FROM testplanmodel 
                WHERE PlanID = %s
                """,
                (plan_id,)
            )
            model_count_result = self.cursor.fetchone()
            model_count = model_count_result[0] if model_count_result else 0

            # 如果没有关联机型，直接返回 0
            if model_count == 0:
                return 0

            # 查询原始用例数量
            self.cursor.execute(
                "SELECT COUNT(*) FROM TestCase WHERE sheet_id IN (SELECT id FROM TestSheet WHERE plan_id=%s)",
                (plan_id,)
                )
            case_count_result = self.cursor.fetchone()
            case_count = case_count_result[0] if case_count_result else 0

            # 总用例数 = 原始用例数 * 关联机型数量
            total_case_count = case_count * model_count
            return total_case_count
        except Exception as e:
            logger.error(f"统计总用例数时发生错误: {e}")
            return 0

    def count_executed_case_by_plan_id(self, plan_id):
        """
        统计已执行用例数
        :param plan_id: 测试计划的 plan_id
        :return: 返回该测试计划中已执行的用例数
        """
        try:
            # 查询已执行用例数，关联 TestExecution 表、TestCase 表 和 TestSheet 表
            query = """
            SELECT COUNT(te.CaseID)
            FROM TestExecution te
            INNER JOIN TestCase tc ON te.CaseID = tc.CaseID
            INNER JOIN TestSheet ts ON tc.sheet_id = ts.id
            WHERE ts.plan_id = %s AND te.TestResult IS NOT NULL
            """
            self.cursor.execute(query, (plan_id,))
            executed_count = self.cursor.fetchone()

            # 如果查询结果存在且不为空，返回已执行用例数
            return executed_count[0] if executed_count else 0
        except Exception as e:
            # 捕获异常，记录日志并返回 0
            logger.error(f"统计已执行用例数时发生错误: {e}")
            return 0

    def count_test_case_results_by_plan_id(self, plan_id):
        """
        统计通过、失败和阻塞的用例
        :param plan_id: 测试计划的 plan_id
        :return: 返回该测试计划中已通过、失败和阻塞的用例数
        """
        try:
            query = """
            SELECT 
                SUM(CASE WHEN te.TestResult = 'Pass' THEN 1 ELSE 0 END) AS pass_count,
                SUM(CASE WHEN te.TestResult = 'Fail' THEN 1 ELSE 0 END) AS fail_count,
                SUM(CASE WHEN te.TestResult = 'Block' THEN 1 ELSE 0 END) AS block_count
            FROM testexecution te
            WHERE te.CaseID IN (
                SELECT tc.CaseID 
                FROM TestCase tc
                WHERE tc.sheet_id IN (
                    SELECT ts.id 
                    FROM TestSheet ts
                    WHERE ts.plan_id = %s
                )
            )
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

    def select_project_name_by_id(self, sheet_id):
        query = """
        SELECT tp.project_name FROM testplan tp JOIN IN testsheet ts
        ON tp.id = ts.plan_id 
        WHERE ts.id = %s
        """
        self.cursor.execute(query, (sheet_id,))
        result = self.cursor.fetchone()
        logger.info(result)
        return {'project_name': result[0]}

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
        tester = self.select_tester_by_plan_or_sheet(plan_id=plan_id)
        logger.warning(case_time_count)
        logger.warning(workloading_time)
        logger.warning(case_count)
        logger.warning(executed_cases_count)
        logger.warning(result_count)

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
            "workloading_time": workloading_time,
            "tester": tester
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
            "workloading_time": workloading_time,
            "tester": tester
        }

    def select_start_time(self, model_id, case_id):
        logger.info(f"接收 model_id: {model_id}, case_id: {case_id}")
        self.cursor.execute(
            "SELECT StartTime FROM testexecution WHERE ModelID = %s AND CaseID = %s",
            (model_id, case_id)
        )
        result = self.cursor.fetchone()
        logger.warning(result)

        if result:
            logger.info(f"查询成功，StartTime: {result[0]}")
            return result[0]  # 返回具体的 StartTime 值
        else:
            logger.warning("未找到匹配的执行记录")
            return None

    def select_tester_by_plan_or_sheet(self, plan_id=None, sheet_id=None):
        if sheet_id:
            # 暂时不删这个逻辑
            query = "SELECT tester FROM TestSheet WHERE id = %s"
            self.cursor.execute(query, (sheet_id,))
        else:
            query = """
            SELECT DISTINCT u.username
            FROM users u
            JOIN testplan tp ON u.userId = tp.userId
            WHERE tp.id = %s;
            """
            self.cursor.execute(query, (plan_id,))
        result = self.cursor.fetchall()
        logger.info(result)
        return [tester[0] for tester in result]

    def select_test_phase(self, plan_id):
        query = "SELECT project_phase FROM testplan WHERE id = %s"
        self.cursor.execute(query, (plan_id,))
        result = self.cursor.fetchone()
        logger.info(result)
        return result[0]

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

    def update_project_workloading_tester(self, plan_name, project=None, workloading=None, tester=None, sheet_id=None):
        # 建立动态更新的 SQL 语句
        fields_to_update = []
        params = []
        if project:
            fields_to_update.append("project = %s")
            params.append(project)
        if workloading:
            fields_to_update.append("workloading = %s")
            params.append(workloading)
        if tester:
            fields_to_update.append("tester = %s")
            params.append(tester)
        # 如果没有要更新的字段，直接返回
        if not fields_to_update:
            logger.warning("没有要更新的字段")
            return
        # 更新 testsheet 表
        if sheet_id:
            update_query = f"UPDATE testsheet SET {', '.join(fields_to_update)} WHERE id = %s"
            logger.warning("仅更新sheet")
            logger.warning(update_query)
            params.append(sheet_id)
        else:
            plan_id = self.select_plan_id(plan_name)
            update_query = f"UPDATE testsheet SET {', '.join(fields_to_update)} WHERE plan_id = %s"
            logger.warning("更新所有计划")
            logger.warning(update_query)
            params.append(plan_id)
        self.cursor.execute(update_query, params)

    def upload_image_file(self, execution_id, original_filename, stored_filename, s3_key, file_size, mime_type):
        # 执行插入操作
        self.cursor.execute(
            """
            INSERT INTO testcase_image (ExecutionID, OriginalFileName, StoredFileName, FilePath, FileSize, MimeType, UploadDate)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (execution_id, original_filename, stored_filename, s3_key, file_size, mime_type, datetime.now()))

        # 获取最后插入的ID
        self.cursor.execute("SELECT LAST_INSERT_ID()")
        image_id = self.cursor.fetchone()[0]
        return image_id

    def insert_execution_with_image(self, case_id, model_id, case_result, images_data, comment=None):
        # 查询执行记录
        result = self.select_start_time(model_id, case_id)
        if result is None:
            raise logger.error("未找到匹配的测试执行记录")

        # 获取ExecutionID
        self.cursor.execute(
            "SELECT ExecutionID FROM testexecution WHERE CaseID = %s AND ModelID = %s",
            (case_id, model_id)
        )
        execution_id = self.cursor.fetchone()
        if execution_id is None:
            raise logger.error("无法获取执行的 ExecutionID")

        # 计算测试耗时
        now = datetime.now()
        test_time = int((now - result).total_seconds())
        logger.info(f"测试消耗时间是 {test_time}")
        formatted_now = now.strftime('%Y-%m-%d %H:%M:%S')

        # 开始事务
        self.cursor.execute("BEGIN")
        # 更新测试结果
        self.cursor.execute(
            "UPDATE testexecution SET EndTime = %s, TestTime = %s, TestResult = %s WHERE ExecutionID = %s",
            (formatted_now, test_time, case_result, execution_id[0])
        )
        # 插入评论
        if comment:
            logger.warning("开始插入评论................................")
            self.cursor.execute(
                "INSERT INTO TestCaseComments (ExecutionID, Comment, CommentTime) VALUES (%s, %s, %s)",
                (execution_id[0], comment, formatted_now)
            )
            # 重新计算 FailCount
            self.cursor.execute(
                "SELECT Comment FROM TestCaseComments WHERE ExecutionID = %s",
                (execution_id[0],)
            )
            comments = [row[0] for row in self.cursor.fetchall()]
            logger.warning(comments)
            fail_count = sum(c.count('Fail') for c in comments)
            block_count = sum(c.count('Block') for c in comments)

            # 更新 FailCount 字段
            self.cursor.execute(
                "UPDATE testexecution SET FailCount = %s, BlockCount = %s WHERE ExecutionID = %s",
                (fail_count, block_count, execution_id[0])
            )
            logger.warning("插入结束................................")
        # 插入 testcase_image 表
        for image_data in images_data:
            self.cursor.execute(
                "INSERT INTO testcase_image (ExecutionID, OriginalFileName, StoredFileName, FilePath, FileSize, MimeType, UploadDate) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                (execution_id[0], image_data['original_file_name'], image_data['stored_file_name'],
                 image_data['file_path'], image_data['file_size'], image_data['mime_type'], formatted_now)
            )
        logger.info(f"插入成功，ExecutionID: {execution_id[0]}")

        return execution_id[0]

    def select_execution_ids(self, case_ids, model_id):
        # 创建占位符字符串
        placeholders = ', '.join(['%s'] * len(case_ids))

        query = f"""
        SELECT ExecutionID
        FROM testexecution
        WHERE CaseID IN ({placeholders}) AND ModelID = %s
        """

        # 将 case_ids 展开为参数列表
        self.cursor.execute(query, (*case_ids, model_id))
        execution_ids = self.cursor.fetchall()
        logger.info(execution_ids)
        return [execution_id[0] for execution_id in execution_ids]

    def select_images_by_execution_id(self, execution_id):
        query = """
        SELECT * FROM testcase_image WHERE ExecutionID = %s
        """
        self.cursor.execute(query, (execution_id,))
        images = self.cursor.fetchall()
        logger.warning(images)
        return images

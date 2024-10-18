import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from flask import Flask, request, jsonify
from common.logs import logger
from mysql.connector.pooling import MySQLConnectionPool
from patvsweb_services.sql_manager import TestCaseManager
from functools import wraps
import jwt
import datetime
import re

app = Flask(__name__)
app.config['SECRET_KEY'] = 'lenovo_secret_key'
# 数据库配置
# DB_CONFIG = {
#     'host': os.getenv('DB_HOST'),
#     'user': os.getenv('DB_USER'),
#     'password': os.getenv('DB_PASSWORD'),
#     'database': os.getenv('DB_DATABASE'),
#     'buffered': True
# }

# 生产
# DB_CONFIG = {
#     'host': '10.196.155.148',
#     'user': 'a_appconnect',
#     'password': 'dHt6BGB4Zxi^',
#     'database': 'patvs_db',
#     'buffered': True
# }

# test
DB_CONFIG = {
    'host': '10.196.155.148',
    'user': 'a_appconnect',
    'password': 'dHt6BGB4Zxi^',
    'database': 'patvs_test',
    'buffered': True
}
db_pool = MySQLConnectionPool(pool_name="mypool", pool_size=10, **DB_CONFIG)


def get_db_connection():
    return db_pool.get_connection()


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('x-access-tokens')
        if not token:
            return jsonify({'error': 'Token is missing!'}), 403
        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            current_user = data['username']
            logger.warning(current_user)
        except:
            return jsonify({'error': 'Token is invalid!'}), 403
        return f(*args, current_user=current_user, **kwargs)

    return decorated


@app.route('/update_start_time', methods=['POST'])
@token_required
def update_start_time(current_user):
    data = request.json
    case_id = data.get('case_id')
    actions = data.get('actions')
    logger.info(f"Updating start time for case_id: {case_id}, actions: {actions}")
    if not case_id or not actions:
        return jsonify({'error': 'Missing required parameters'}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        manager = TestCaseManager(conn, cursor)
        manager.update_start_time_by_case_id(case_id, actions)
        conn.commit()
        return jsonify({'message': 'Start time updated successfully.'}), 200
    except Exception as e:
        conn.rollback()
        logger.error(f"An error occurred: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@app.route('/update_end_time', methods=['POST'])
@token_required
def update_end_time(current_user):
    data = request.json
    case_id = data.get('case_id')
    case_result = data.get('case_result')
    comment = data.get('comment', None)
    logger.info(f"Updating start time for case_id: {case_id}, actions: {case_result}, comment: {comment}")
    if not case_id or not case_result:
        return jsonify({'error': 'Missing required parameters'}), 400
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        manager = TestCaseManager(conn, cursor)
        manager.update_end_time_case_id(case_id, case_result, comment)
        conn.commit()
        return jsonify({'message': 'End time updated successfully.'}), 200
    except Exception as e:
        conn.rollback()
        logger.error(f"An error occurred: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@app.route('/insert_case', methods=['POST'])
@token_required
def insert_case(current_user):
    data = request.json
    plan_name = data.get('plan_name')
    project_name = data.get('project_name')
    sheet_name = data.get('sheet_name')
    tester = data.get('tester')
    workloading = data.get('workloading')
    filename = data.get('filename')
    cases = data.get('cases')
    model_name = data.get('model_name')

    logger.info(f"Inserting case for plan: {plan_name}, project: {project_name}, sheet: {sheet_name}")

    if not plan_name or not project_name or not sheet_name or not tester or not workloading or not filename or not cases or not model_name:
        return jsonify({'error': 'Missing required parameters'}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        manager = TestCaseManager(conn, cursor)
        manager.insert_case_by_filename(plan_name, project_name, sheet_name, tester, workloading, filename, cases,
                                        model_name)
        conn.commit()
        return jsonify({'message': 'Case inserted successfully.'}), 200
    except Exception as e:
        conn.rollback()
        logger.error(f"An error occurred: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@app.route('/insert_case_by_power', methods=['POST'])
@token_required
def insert_case_by_power(current_user):
    data = request.json
    project_name = data.get('project_name')
    sheet_name = data.get('sheet_name')
    tester = data.get('tester')
    workloading = data.get('workloading')
    filename = data.get('filename')
    cases = data.get('cases')

    logger.info(f"Inserting case for file: {filename}, project: {project_name}, sheet: {sheet_name}")

    if not project_name or not sheet_name or not tester or not workloading or not filename or not cases:
        return jsonify({'error': 'Missing required parameters'}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        manager = TestCaseManager(conn, cursor)
        manager.insert_case_by_power_filename(filename, sheet_name, project_name, tester, workloading, cases)
        conn.commit()
        return jsonify({'message': 'Case inserted successfully.'}), 200
    except Exception as e:
        conn.rollback()
        logger.error(f"An error occurred: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@app.route('/get_cases/<int:sheet_id>', methods=['GET'])
def get_cases(sheet_id):
    logger.info(f"Fetching cases for sheet_id: {sheet_id}")
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        manager = TestCaseManager(conn, cursor)
        cases = manager.select_case_by_sheet_id(sheet_id)
        formatted_cases = []
        for case in cases:
            case_list = list(case)
            case_list[8] = case_list[8].strftime('%Y-%m-%d %H:%M:%S') if case_list[8] else None
            case_list[9] = case_list[9].strftime('%Y-%m-%d %H:%M:%S') if case_list[9] else None
            formatted_cases.append(case_list)

        return jsonify({case[12]: case for case in formatted_cases}), 200
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@app.route('/get_comments', methods=['POST'])
def get_comments_for_case():
    data = request.json
    case_ids = data.get('case_ids')
    logger.info(f"Fetching cases for case_ids: {case_ids}")
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        manager = TestCaseManager(conn, cursor)
        comments = manager.select_all_comments(case_ids)
        return jsonify({'comments': comments}), 200
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@app.route('/get_plan_names/<string:username>', methods=['GET'])
def get_plan_names(username):
    logger.info(f"Fetching plan names for username: {username}")
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        manager = TestCaseManager(conn, cursor)
        plan_names = manager.select_all_plan_names_by_username(username)
        return jsonify({'plan_names': plan_names}), 200
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@app.route('/get_plan_names_by_admin', methods=['GET'])
def get_plan_names_by_admin():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        manager = TestCaseManager(conn, cursor)
        plan_names = manager.select_all_plan_names()
        return jsonify({'plan_names': plan_names}), 200
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@app.route('/get_sheet_names', methods=['GET'])
def get_sheet_names():
    username = request.args.get('username')
    plan_name = request.args.get('plan_name')
    logger.info(f"Fetching sheet names for username: {username} and plan_name: {plan_name}")
    if not username or not plan_name:
        return jsonify({'error': 'Missing required parameters'}), 400
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        manager = TestCaseManager(conn, cursor)
        sheet_names_with_ids = manager.select_all_sheet_names_by_plan_and_username(plan_name, username)
        return jsonify({'sheet_names_with_ids': sheet_names_with_ids}), 200
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@app.route('/get_sheet_names_by_admin/<string:plan_name>', methods=['GET'])
def get_sheet_names_by_admin(plan_name):
    logger.info(f"Fetching sheet names for plan_name: {plan_name}")
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        manager = TestCaseManager(conn, cursor)
        sheet_names_with_ids = manager.select_all_sheet_names_by_plan(plan_name)
        return jsonify({'sheet_names_with_ids': sheet_names_with_ids}), 200
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@app.route('/get_userid/<string:username>', methods=['GET'])
def get_userid(username):
    logger.info(f"Fetching user ID for username: {username}")
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        manager = TestCaseManager(conn, cursor)
        user_id = manager.select_userid_by_username(username)
        return jsonify({'user_id': user_id}), 200
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@app.route('/get_filename/<string:filename>', methods=['GET'])
def get_filename(filename):
    logger.info(f"Fetching filename: {filename}")
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        manager = TestCaseManager(conn, cursor)
        file_exists = manager.select_filename_by_filename(filename)
        return jsonify({'file_exists': file_exists}), 200
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@app.route('/get_plan_name_by_planname/<string:plan_name>', methods=['GET'])
def get_plan_name_by_planname(plan_name):
    logger.info(f"Fetching plan_name: {plan_name}")
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        manager = TestCaseManager(conn, cursor)
        plan_exists = manager.select_plan_name_by_plan_name(plan_name)
        return jsonify({'plan_exists': plan_exists}), 200
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@app.route('/get_plan_name/<string:filename>', methods=['GET'])
def get_plan_name(filename):
    logger.info(f"Fetching plan name for filename: {filename}")
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        manager = TestCaseManager(conn, cursor)
        plan_name = manager.select_plan_name_by_filename(filename)
        return jsonify({'plan_name': plan_name}), 200
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@app.route('/get_cases_by_case_id/<int:case_id>', methods=['GET'])
def get_cases_by_case_id(case_id):
    logger.info(f"Fetching cases for case_id: {case_id}")
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        manager = TestCaseManager(conn, cursor)
        cases = manager.select_cases_by_case_id(case_id)
        formatted_cases = []
        for case in cases:
            case_list = list(case)
            case_list[8] = case_list[8].strftime('%Y-%m-%d %H:%M:%S') if case_list[8] else None
            case_list[9] = case_list[9].strftime('%Y-%m-%d %H:%M:%S') if case_list[9] else None
            formatted_cases.append(case_list)
        return jsonify({'cases': formatted_cases}), 200
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@app.route('/update_test_num', methods=['POST'])
@token_required
def update_test_num(current_user):
    data = request.json
    case_id = data.get('case_id')
    test_num = data.get('test_num')

    logger.info(f"Updating test number for case_id: {case_id}")

    if not case_id or not test_num:
        return jsonify({'error': 'Missing required parameters'}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        manager = TestCaseManager(conn, cursor)
        manager.update_test_num_by_id(test_num, case_id)
        conn.commit()
        return jsonify({'message': 'Test number updated successfully.'}), 200
    except Exception as e:
        conn.rollback()
        logger.error(f"An error occurred: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@app.route('/get_test_num/<int:case_id>', methods=['GET'])
def get_test_num(case_id):
    logger.info(f"Fetching cases for case_id: {case_id}")
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        manager = TestCaseManager(conn, cursor)
        test_num = manager.select_test_num_by_id(case_id)
        return jsonify({'test_num': test_num}), 200
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@app.route('/get_case_result/<int:case_id>', methods=['GET'])
def get_case_result(case_id):
    logger.info(f"Fetching cases for case_id: {case_id}")
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        manager = TestCaseManager(conn, cursor)
        case_result = manager.select_case_result_by_id(case_id)
        return jsonify({'case_result': case_result}), 200
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@app.route('/reset_case_result', methods=['POST'])
@token_required
def reset_case_result(current_user):
    data = request.json
    case_id = data.get('case_id')
    logger.info(f"Fetching cases for case_id: {case_id}")
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        manager = TestCaseManager(conn, cursor)
        manager.reset_case_by_case_id(case_id)
        conn.commit()
        return jsonify({'message': 'Test case reset successfully.'}), 200
    except Exception as e:
        conn.rollback()
        logger.error(f"An error occurred: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@app.route('/calculate_progress_and_pass_rate/<int:sheet_id>', methods=['GET'])
def calculate_progress_and_pass_rate(sheet_id):
    logger.info(f"Fetching sheets for sheet_id: {sheet_id}")
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        manager = TestCaseManager(conn, cursor)
        result = manager.calculate_progress_and_pass_rate(sheet_id)
        return jsonify({'result': result}), 200
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@app.route('/calculate_plan_statistics/<int:plan_id>', methods=['GET'])
def calculate_plan_statistics(plan_id):
    logger.info(f"Fetching plan for plan_id: {plan_id}")
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        manager = TestCaseManager(conn, cursor)
        result = manager.calculate_plan_statistics(plan_id)
        return jsonify({'result': result}), 200
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@app.route('/get_start_time/<int:case_id>', methods=['GET'])
def get_start_time(case_id):
    logger.info(f"Fetching start_time for case_id: {case_id}")
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        manager = TestCaseManager(conn, cursor)
        start_time = manager.select_start_time(case_id)
        if start_time:
            # Convert datetime object to string
            start_time = start_time.strftime('%Y-%m-%d %H:%M:%S')
        logger.warning(start_time)
        return jsonify({'start_time': start_time}), 200
    except Exception as e:
        conn.rollback()
        logger.error(f"An error occurred: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@app.route('/get_plan_id/<string:plan_name>', methods=['GET'])
def get_plan_id(plan_name):
    logger.info(f"Fetching plan_id for plan_name: {plan_name}")
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        manager = TestCaseManager(conn, cursor)
        plan_id = manager.select_plan_id(plan_name)
        conn.commit()
        return jsonify({'plan_id': plan_id}), 200
    except Exception as e:
        conn.rollback()
        logger.error(f"An error occurred: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@app.route('/add_user', methods=['POST'])
def add_user():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    role = data.get('role', None)
    logger.info(f"add uesr by username: {username}, password: {password} ")

    if not username or not password:
        return jsonify({'error': 'Missing required parameters'}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        manager = TestCaseManager(conn, cursor)
        manager.add_user(username, password, role)
        conn.commit()
        return jsonify({'message': f'add user {username} successfully.'}), 200
    except Exception as e:
        conn.rollback()
        logger.error(f"An error occurred: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@app.route('/login', methods=['POST'])
def validate_user():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    logger.info(f"login username: {username}, password: {password} ")

    if not username or not password:
        return jsonify({'error': 'Missing required parameters'}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        manager = TestCaseManager(conn, cursor)
        valid, role = manager.validate_user(username, password)
        if valid:
            token = jwt.encode({
                'username': username,
                'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
            }, app.config['SECRET_KEY'], algorithm="HS256")
            return jsonify({'token': token, 'role': role})
        else:
            return jsonify({'error': 'Invalid credentials'}), 401
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@app.route('/change_user_password', methods=['POST'])
def change_user_password():
    data = request.json
    username = data.get('username')
    old_password = data.get('old_password')
    new_password = data.get('new_password')
    logger.info(
        f"change_user_password username: {username}, old_password: {old_password} , new_password: {new_password}")

    if not username or not old_password or not new_password:
        return jsonify({'error': 'Missing required parameters'}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        manager = TestCaseManager(conn, cursor)
        result = manager.change_user_password(username, old_password, new_password)
        return jsonify({'result': result}), 200
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@app.route('/get_tester', methods=['GET'])
def get_tester():
    plan_name = request.args.get('plan_name')
    sheet_id = request.args.get('sheet_id')
    logger.info(f"get_tester plan_name: {plan_name}, sheet_id: {sheet_id} ")

    # if not plan_name or not sheet_id:
    #     return jsonify({'error': 'Missing required parameters'}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        manager = TestCaseManager(conn, cursor)
        tester = manager.select_tester_by_plan_or_sheet(plan_name, sheet_id)
        return jsonify({'tester': tester}), 200
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@app.route('/get_case_actions_and_num/<int:case_id>', methods=['GET'])
def get_case_actions_and_num(case_id):
    logger.info(f"get_case_actions_and_num case_id: {case_id} ")

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        manager = TestCaseManager(conn, cursor)
        title = manager.select_case_title(case_id)
        logger.info(title)
        # "[S3+5][S4+6][S5+3]N5(03)BT Pairing multi devices BT多设备配对"
        # 提取[]括号内的内容
        bracket_contents = re.findall(r'\[([^\]]+)\]', title)
        logger.warning(bracket_contents)
        # 提取关键参数
        key_params = []
        for content in bracket_contents:
            matches = re.match(r'(.+?)\+(\d+)', content)
            if matches:
                key_params.append((matches.group(1), matches.group(2)))
        logger.warning(key_params)
        return jsonify({'actions_and_num': key_params}), 200
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@app.route('/update_project_workloading_tester', methods=['POST'])
def update_project_workloading_tester():
    data = request.json
    plan_name = data.get('plan_name')
    project_name = data.get('project_name', None)
    workloading = data.get('workloading', None)
    tester = data.get('tester', None)
    sheet_id = data.get('sheet_id', None)
    logger.info(
        f"update_project_workloading_tester plan_name: {plan_name}")

    if not plan_name:
        return jsonify({'error': 'Missing required parameters'}), 400
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        manager = TestCaseManager(conn, cursor)
        if tester:
            res = manager.select_userid_by_username(tester)
            if not res:
                return jsonify({'message': f'你输入的用户 {tester} 不存在'}), 400
        manager.update_project_workloading_tester(plan_name, project_name, workloading, tester, sheet_id)
        conn.commit()
        return jsonify({'message': 'success'}), 200
    except Exception as e:
        conn.rollback()
        logger.error(f"An error occurred: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@app.route('/hello', methods=['GET'])
def get_hello():
    return jsonify({'tester': "hello,hello,hello,hello,hello。网络是通的。"}), 200


if __name__ == '__main__':
    app.run(debug=True, host='10.184.32.52', port=80)

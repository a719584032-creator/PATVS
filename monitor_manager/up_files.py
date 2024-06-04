from openpyxl import load_workbook
from openpyxl import Workbook
from common.rw_excel import MyExcel
from common.logs import logger
from sql_manager.patvs_sql import Patvs_SQL
import os

# 检查合并单元格是否符合特定规则
def is_merged_within_range(merged_ranges, row, start_col, end_col):
    for rng in merged_ranges:
        # 检查传入的行号是否在某个合并单元格的范围内，同时列号也要在指定的合并列范围内。
        if row >= rng.min_row and row <= rng.max_row and start_col >= rng.min_col and end_col <= rng.max_col:
            return True
    return False


def get_all_test(file_name, sheet_name):
    """
    获取所有用例，按照指定格式[A-F合并为用例标题，A-D列合并为用例步骤，D-F合并为预期结果]
    """
    workbook = load_workbook(file_name)
    sheet = workbook[sheet_name]
    # 获取工作表中所有合并单元格的范围信息，并存入merged_ranges列表。
    merged_ranges = list(sheet.merged_cells.ranges)
    # 获取第19行机型数据
    row_19_data = [cell.value for cell in sheet[19] if cell.value is not None]
    model_name = row_19_data[2:]

    # 初始化用例信息存储结构
    case = {
        'title': None,
        'steps': None,
        'expected': None
    }
    all_case = []
    current_title = None
    # 遍历工作表中的所有行
    for row in range(20, sheet.max_row + 1):

        # 检查是否是标题行：A-F列中只有此行数据
        if is_merged_within_range(merged_ranges, row, 1, 6):
            title_cell = sheet.cell(row, 1)
            current_title = title_cell.value
            continue  # 跳过后续步骤，继续下一行

        # 检查是否是步骤：A-D列合并
        if is_merged_within_range(merged_ranges, row, 1, 4):
            steps_cell = sheet.cell(row, 1)
            case['steps'] = steps_cell.value
        # 检查是否是预期结果：E-F列合并
        if is_merged_within_range(merged_ranges, row, 5, 6):
            expected_cell = sheet.cell(row, 5)
            case['expected'] = expected_cell.value
            # 过滤掉都为 None 的数据，添加后重置字典
            if any(case.values()):
                filled_case = {
                    'title': current_title if current_title is not None else 'NA',
                    'steps': case['steps'] if case['steps'] is not None else 'NA',
                    'expected': case['expected'] if case['expected'] is not None else 'NA'
                }
                all_case.append(filled_case)
                case = {
                    'title': None,
                    'steps': None,
                    'expected': None
                }
    return model_name, all_case


def validate_excel_format(file_name):
    """
    校验 Excel 文件格式
    """
    workbook = load_workbook(file_name)
    required_sheets = ['Plan Information', 'Case List']

    for sheet_name in required_sheets:
        if sheet_name not in workbook.sheetnames:
            raise ValueError(f"缺少必要的 sheet 页: {sheet_name}")

    plan_info_sheet = workbook['Plan Information']
    if plan_info_sheet.cell(1, 1).value != 'Plan name':
        raise ValueError(
            f"Plan Information sheet 页中 A1 单元格的值必须为 'Plan name', 实际值为 {plan_info_sheet.cell(1, 1).value}")

    case_list_sheet = workbook['Case List']
    value = case_list_sheet.cell(1, 2).value
    value.strip().lower()
    if value != 'Case name':
        raise ValueError(
            f"Case List sheet 页中 B2 单元格的值必须为 'Case name', 实际值为 {value}")

    logger.info("文件格式校验通过")
    return True


def run_main(file_name):
    sql = Patvs_SQL()
    validate_excel_format(file_name)
    data = MyExcel(file_name)
    data.active_sheet('Plan Information')
    plan_name = data.get_value_by_rc(1, 2)
    logger.info(f'plan_name is {plan_name}')
    project_name = data.get_value_by_rc(1, 4)
    logger.info(f'project_name is {project_name}')
    data.active_sheet('Case List')
    all_sheet = data.getColValues(2)[2:]
    # 实际 sheet_name 需要加上递增的前缀
    all_sheet_with_prefix = [f'{i + 1}-{val}' for i, val in enumerate(all_sheet)]
    all_tester = data.getColValues(14)[2:]
    all_workloading = data.getColValues(15)[2:]
    logger.info(f'all_sheet_with_prefix is {all_sheet_with_prefix}')
    logger.info(f'all_tester is {all_tester}')
    sheet_and_tester_and_workloading = list(zip(all_sheet_with_prefix, all_tester, all_workloading))
    logger.info(f'sheet_and_tester_and_workloading is {sheet_and_tester_and_workloading}')
    for i in sheet_and_tester_and_workloading:
        model_name, all_case = get_all_test(file_name, i[0])
        sql.insert_case_by_filename(plan_name, project_name, i[0], i[1], i[2], file_name, all_case, model_name)

if __name__ == '__main__':
    file_name = r'D:\PATVS\TestPlanWithResult_M410_Mouse_PATVS软件测试(1)_20240528100806.xlsx'
    run_main(file_name)



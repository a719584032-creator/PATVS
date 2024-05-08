from openpyxl import load_workbook
from openpyxl import Workbook
from common.rw_excel import MyExcel


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
    print(merged_ranges)
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
    # 遍历工作表中的所有行
    for row in range(20, sheet.max_row + 1):

        # 检查是否是标题行：A-F列中只有此行数据
        if is_merged_within_range(merged_ranges, row, 1, 6):
            title_cell = sheet.cell(row, 1)
            print("-" * 40)
            print(f"用例标题: {title_cell.value}")
            case['title'] = title_cell.value
            continue  # 跳过后续步骤，继续下一行

        # 检查是否是步骤：A-D列合并
        if is_merged_within_range(merged_ranges, row, 1, 4):
            steps_cell = sheet.cell(row, 1)
            print(f"用例步骤: {steps_cell.value}")
            case['steps'] = steps_cell.value
        # 检查是否是预期结果：E-F列合并
        if is_merged_within_range(merged_ranges, row, 5, 6):
            expected_cell = sheet.cell(row, 5)
            print(f"预期结果: {expected_cell.value}")
            case['expected'] = expected_cell.value
            print("-" * 40)  # 打印分隔线，表示步骤和预期结果的结束
            # 过滤掉都为 None 的数据，添加后重置字典
            if any(case.values()):
                filled_case = {k: v if v is not None and v != '' else 'NA' for k, v in case.items()}
                print('************************************************')
                print(filled_case['expected'])
                print('************************************************')
                all_case.append(filled_case)
                case = {
                    'title': None,
                    'steps': None,
                    'expected': None
                }
    return model_name, all_case


def save_cases_to_excel(cases, filename, tester, model_name=None):
    """
    写入新的用例格式，按照机型循环写入用例，sheet页面为 tester
    """
    # 创建一个新工作簿和工作表
    wb = Workbook()
    ws = wb.active
    ws.title = tester

    # 添加列标题
    ws.append(['测试机型', '用例标题', '用例步骤', '预期结果'])
    if model_name:
        for m in model_name:
            # 添加用例数据
            for case in cases:
                ws.append([m, case['title'], case['steps'], case['expected']])
    else:
        for case in cases:
            ws.append(['', case['title'], case['steps'], case['expected']])

    # 保存工作簿
    wb.save(filename + '.xlsx')


def run_main(file_name):
    data = MyExcel(file_name)
    data.active_sheet('Case List')
    all_sheet = data.getColValues(2)[2:]
    # 遍历all_sheet列表，给每个值加上递增的前缀
    all_sheet_with_prefix = [f'{i + 1}-{val}' for i, val in enumerate(all_sheet)]
    all_tester = data.getColValues(14)[2:]
    print(all_sheet_with_prefix)
    print(all_tester)
    sheet_and_tester = list(zip(all_sheet_with_prefix, all_tester))
    print(sheet_and_tester)
    # sheet_name = '2-KB test  basic function'
    for i in sheet_and_tester:
        model_name, all_case = get_all_test(file_name, i[0])
        save_cases_to_excel(all_case, i[0], i[1], model_name)


if __name__ == '__main__':
    file_name = 'TestPlanWithResult_K510_Keyboard_K510_Audit_test_20240411173441.xlsx'
    run_main(file_name)
    # data = MyExcel(file_name)
    # data.active_sheet('Case List')
    # sheet_name = '2-KB test  basic function'
    # model_name, all_case = get_all_test(file_name, sheet_name)
    # model = ['qqq', 'mmm']

    # save_cases_to_excel(all_case, sheet_name, 'ysq', model)

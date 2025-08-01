data = {
    "电脑型号T14S": {
        "1-Mouse Scenario test 01": [('case1'), ('case2')],
        "2-XXX": [('case1'), ('case2')],
    },
    "电脑型号T15S": {
        "1-Mouse Scenario test 22": [('case1'), ('case2')],
        "3-XXX": [('case1'), ('case2')],
    },
}

for model_name, sheets in data.items():
    print(f"model_name: {model_name}, sheet_names: {list(sheets.keys())}")

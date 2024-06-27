# PATVS 监控工具
### 1、这是一款监控并管理用户测试用例执行的工具，支持上传用例，并记录用例的执行状态，次数，耗时
### 2、支持监控 Windows S3 S4 S4 RESTART 等等动作，并且用户需要达到指定执行次数后才能修改用例状态
### 3、支持已项目管理的维度，review 整体测试进度
```
## 项目整体结构
├──common 
│   │   
│   ├── logs  # 日志模块封装 
│   │
│   ├── tools  # 常用公共方法封装（随机数、正则匹配）
│   │
│   └── rw_excel # 读写 excel 封装
│
├──monitor_manager 
│   │   
│   ├── devicerm  # usb插拔监控 
│   │   
│   ├── up_files  # 上传文件 
│   │
│   ├── lock_csreen  # 锁屏监控
│   │
│   └── patvs_fuction # S3,S4,S5,RESTART监控
│
├──web_server 
│   │   
│   ├── app.py  # 应用主程序  
│   │
│   ├── sql_manager  # sql管理，数据存储
│   │
│   └── api_manager # API
│     
├── ui_manager  # UI界面模块
│
├── patvs_gui.spec  # exe打包脚本
│ 
├── build/dist  # 打包生成的文件目录
│
└── patvs_gui.py  # 登录、运行入口

```
#install
```angular2html
pip install -r requirements.txt
```

#打包
```angular2html
pyinstaller ./patvs_gui.spec
```

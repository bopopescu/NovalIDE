Changelog
=========

Changes with latest version of NovalIDE
----------------------------------------------

Version 1.0.0 -------------2017-12-23

- support Cross Platform editor
- support HTML,python,text xml lanauge 
- auto load default python interpreter
- find replace text in open document
- find text in directory files
- convinient to install editor in windows and linux system
- auto detect file modified or deleted without editor
- support mru files and delete invalid file path
- enable show tips when startup application
- multi document tabbed frame style
- auto detect python file encoding when save python document
- enable code margin fold style
- simple support debug or run a python script in editor or terminator 


Version 1.0.1 -------------2017-12-27

- enable check python file syntax
- show caret line background color
- enbale open file path in terminator
- set debug or run script execution dir is script path
- support python script path contains chinese
- optimise debug run mode
- enable kill or stop debug run process
- enable debug have stdin input python script
- enable colorize error output or input text
- enable terminate all running process
- change application splash image
- delete ide splash embed bitmap data
- enable user choose one interpreter from multiple choices
- auto analyse intepreter interllisence data
- go to definition of text


Version 1.0.2 -------------2018-01-08

- implement go to word definition in global scope search
- interligent analyze class self property in class object method
- remove duplicate child name of class object property
- find definition in document scope
- enable sort in outline service
- enable custom context menu in debug output tab,and enable word wrap in line
- can only launch one find or replace dialog instance
- enable to add one interpreter to editor
- add configure interpreter function
- display interpreter sys path list ,builtin modules and environment
- make install packages run in windows system
- show smart analyse progress dialog
- implement file resource view
- enable find location in outline view
- initial implement code completion
- import and from import code completion
- complete type object completion 


Version 1.0.3 -------------2018-01-16

- smart show module and class member completion
- recognize python base type object and show it's member info
- set intellisense database version
- set virtual scope with database members file
- show progress dialog whhen find text in files
- repair search text progress dialog bug
- enable set script parameter and environment
- support create unit test frame of script
- repair py2exe call subprocess.popen error
- repair cannot inspect cp936 encoding error
- add insert and advance edit function
- separate common intellisense data path and builtin intellisense data,which on linux system ,they are not equal
- add builtin intellisense data to linux build package
- enable insert date,comment template and python coding declare to text
- enable gotodef and listmembers shortcut in menu item
- default use right edge mode in text document
- set xml and html parser fold style
- support parse relative import 
- repair relative import position bug
- upgrade intellisense database generation and update database version to 1.0.2
- support go to defition of from import modules and their childs
- optimise memberlist sort algorithm


Version 1.0.4 -------------2018-02-04

- repair show tip bug
- repair open all files bug in linux system
- auto analyse sys moudles intellisense data
- improve and supplement chinese translation
- smart anlalyse class base inherited classes members
- analyse from import members
- update install instructions on linux system of readme
- allow user choose line eol mode
- add icon to Python Interpreter and Search Result,Debug View
- enable click plus button of dir tree to expand child item in resource view
- supplement chinese translation of wx stock id items
- repair bug when load interpreters and set first add interpreter as default interpreter
- repair check syntax bug in python2.6
- partly support smart analyse interpreter data of python3 version
- optimise outline load parse data mechanism and repair load file bug
- implement new auto completion function of menu item
- fix package install bug on linux os
- fix serious bug when load python3 interprter and smart analyse its data when convert to windows exe with py2exe
- add debug mode which will be convert to console exe with py2exe
- prevent pop warn dialog when the windows exe program exit which is converted by py2exe
- fix 'cannot import name Publisher' error when use py2exe convert to windows exe
- fix run python script which path has chinese character on linux os
- close threading.Thread VERBOSE mode in debugger service
- increase mru history file count from 9 to 20 and allow user to set the max MRU item count
- fix right up menu of document position
- fix bug when run script path contain chinese character on windows os


Version 1.0.5 -------------2018-02-13

- enable to open current python interpreter on tools menu
- allow user to set use MRU menu or not
- implement navigation to next or previous position
- analyse class static members intellisense data
- analyse class and function doc declaration
- simple implement project creation
- analyse builtin member doc declaration and show its calltip information
- separate builtin intellisense data to python 2 and 3
- repair python3 parse function args bug
- fix autoindent bug when enter key is pressed
- Sets when a backspace pressed should do indentation unindents
- modify project document definition ,add project name and interpreter to it 
- fix the error of set progress max range when search text in dir 
- enable set enviroment variable of interpreter when debug or run python script
- fix output truncated error when debug python script 
- add function and class argment show tip
- fix application exit bug when interpreter has been uninstalled
- fix the bug of subprocess.popen run error on some computer cause application cann't startup
- set calltip background and foreground color
- fix the bug when debug run python window program the window interface is hidden
- show python interpreter pip package list in configuration
- disable or enable back delete key when debug output has input according to the caret pos
- when load interpreter configuation list,at least select one interprter in datalist view control
- fix get python3 release version error,which is alpha,beta,candidate and final version

Version 1.0.6 -------------2018-03-6

- add drive icon and volument name on resource view
- use multithread to load python pip package
- fix image view display context menu bug
- change python and text file icon
- add project file icon to project and show project root
- show local icon of file when scan disk file on resource view
- when add point and brace symbol to document text will delete selected text
- save folder open state when swith toggle button on resource view
- parse main function node and show main function in outline view
- fix parse file content bug where content encoding is error
- fix parse collections package recursive bug in python3
- when current interpreter is analysing,load intellisense data at end
- try to get python help path in python loation if help path is empty on windows os
- fix image size is not suitable which will invoke corruption on linux os.convernt png image to 16*16
- fix the bug when click the first line of search results view
- allow add or remove python search path,such as directory,zip ,egg and wheel file path
- add new python virtual env function
- fix environment variable contains unicode character bug
- fix add python virtual env bug on linux os
- fix the bug when double click the file line and show messagebox which cause wxEVT_MOUSE_CAPTURE_LOST problem
- adjust the control layout of configuration page
- remove the left gap if python interpreter view
- allow load builtin python interpreter
- enable debug file in python interpreter view with builtin interpreter
- optimise the speed of load outline of parse tree
- change startup splash image of application
- fix bug when show startup splash image on linux os

Version 1.0.7 -------------2018-03-23

- query the running process to stop or not when application exit
- fix the bug when the interpreter path contain empty blank string
- add icon of unittest treectrl item
- add import files to project and show import file progress
- beautify unittest wizard ui interface
- add new project wizard on right menu of project view
- fix the bug of import files on linux os
- fix the coruption problem of debug run script with builtin interpreter
- fix the bug of open file in file explower on windows os
- optimise and fix bug of import project files
- copy files to project dest dir when import files
- fix the bug when load saved projects
- show prompt message dialog when the import files to project have already exist
- enable filter file types when import files to project 
- fix getcwd coruption bug on linux os when currrent path is deleted
- fix file observer bug on linux os when the watched path is deleted
- add open project and save project memu item on project menu and implement the menu action
- add monitor to currrent project to generate intellisense data of the project
- add project icon of NovalIDE project file with the .nov file extension and associated with NovalIDE application
- enable click on the .nov file to open NovalIDE project
- enable add ,delete and manage breakpoints
- enable add package folder in project
- correct the error number count of search text result in project
- enable open project from command line and set as current project
- update nsis script to write project file extension and icon to regsitry
- fix the serious bug of close and delete project
- enable filter file types when import files to project
- fix the bug of project file or path contains chinese character

Version 1.0.8 -------------2018-04-01

- fix create virtualenv bug on linux os
- fix the bug of file watcher when save as the same file
- update english to chinese translation
- replace toolbar old image with new image
- fix a serious breakpoint debug bug
- add icon to meneu item
- enable install and uninstall package
- add breakpoint debug menu item
- show detail progress information of install and uninstall package
- fix the bug of goto definition bug
- fix the bug of kill process fail on linux os
- kill the smart analyse processes when application exit and smart analyse is running
- add project id attribute to project instance
- enable mutiple selections on project files
- delete project regkey config when close project or delete project
- show styled text of binary document
- show file encoding of document on status bar
- save document cache position when close frame and load position data when open document
- enable modify project name with label edit
- set the startup script of project and bold the project startup item
- enable run and debug last settings of project or file
- fix the bug of create unittest when parse file error
- fix the check syntax error of python script bug
- save all open project documents before run
- fix the bug of close all run tabs
- fix the bug of save chinese text document
- allow set the default file encoding of text document
- fix the bug of pip path contains blank when install and uninstall package
- fix the bug of close debugger window when application exit


Version 1.1.0 -------------2018-05-16

- fix the bug of deepcopy run parameter iter attribute
- create novalide web server project
- enable check for app update version on menu item
- enable download update version from web server
- establish the simple novalide web server
- enable delete files and folder from proeject and local file system
- check update version info when application start up
- support install package with pip promote to root user on linux os
- set default logger debug level to info level
- close open project files when delete project files or folders
- support auto check ,download and install new version of app on linux os
- enable rename folder and file item of project
- when renane folder of project,rename the open folder files
- watch the project document,and alarm the document change event
- fix the bug of load python when app startup on some computer
- fix the bug of null encoding when set file encoding
- enable copy and cut files of project,and paste to another position
- add csv module to library zip when use py2exe to pack
- allow add python package folder to project folder item
- fix a bug of load python interpreter from config
- enable drag file items to move files of project to dest
- fix the save as document bug whe the save as document filename is already opened

Version 1.1.1 -------------2018-05-26

- 菜单添加访问官方网站入口
- 允许用户删掉软件自带解释器（内建），只保留一个非内建解释器
- 添加当前文档到工程时，同时修改当前文档路径并优化处理方式
- 设置关闭文档快捷键
- 优化nsis安装脚本，生成带版本号名称的安装包,卸载包时保留智能提示数据文件
- 优化中文文件编码，修复默认ascii文件不能保存中文字符的问题
- 区分python2和python3编码方式处理，python2包含中文保存文件时自动提示输入编码声明，python3不需要
- 文本文件另存为时可以选择任何文件后缀类型以及文本后缀类型
- 修复另存文本文件的bug
- 修复运行脚本时脚本目录不存成导致程序异常的BUG
- 项目名称为空时自动恢复正常，取消弹出警告对话框
- 支持在软件中添加扩展工具，并在菜单显示扩展工具项
- 添加web浏览器功能
- 支持工程中添加新建文件，并支持模板编辑功能
- 安装包提供中英文选择界面
- 修复项目没有选中任何项时导入文件和新建文件菜单崩溃的BUG，默认设置选中为跟节点
- 修复默认设置python文件编码为非asc时，保存asc编码文件提示插入中文编码的BUG

Version 1.1.2 -------------2018-06-14
- 重新优化调整中英文翻译
- 工程项目添加打开所在文件夹，复制完整路径，打开命令行终端3个功能键
- 打开文件夹或者打开终端失败弹出提示错误信息
- 修改linux系统下默认配置文件夹路径
- 修复linux下安装脚本错误
- 允许设置启动时是否自动检查版本更新
- 资源视图添加打开所在文件夹，复制完整路径，打开命令行终端3个功能菜单，并且允许刷新文件夹内容
- 修复脚本缺少图片的错误以及资源视图BUG
- 修改工具选项设置的界面显示，使用树形方式显示选项设置页面
- 优化解释器配置界面布局显示,更美观合理
- 添加了一些菜单项的图标
- 添加了对yml,ini,css,js,c/c++文件的语法高亮支持
- 增加一些如css,js,c/c++,ini文件类型的图标并修改了不支持文件类型的图标
- 添加了语法高亮主题设置的功能，可以选择任意一种软件包含的主题
- 优化了文件类型模板支持的功能，并能自由添加或扩展任意一种支持的文件类型
- 剔除了一些文件类型重复选项设置面板
- 优化了一些选项设置的功能
- 选择设置里面可以自由更改语法高亮的颜色和字体，并保存设置，下一次启动设置有效
- 支持文件模板编辑与管理
- 文档右键添加新建模块功能
- 对只允许数字的文本输入添加数字校验
- 支持新建并保存模板
- 支持设置字体大小，颜色，粗体，下划线,以及主题等。
- 允许恢复默认语法字体设置
- 编辑器右键菜单添加图标
- 文档右键和选项卡菜单添加图标和快捷键
- 更改运行和调试图标

Version 1.1.3 -------------2018-08-19
- 更改c++文件图标
- 添加切换断点，以及书签的菜单图标
- 新增断点调试的菜单，如逐过程，逐语句，终止调试，只执行不调试等
- 调试程序添加重新启动功能
- 优化运行环境配置，针对每个运行脚本都有独立的环境配置
- 工程右键和文档右键菜单添加运行和调试功能菜单
- 支持Python3断点调试，包括逐语句，逐过程，中断，停止调试，跳出，继续执行等调试功能
- 设置断点调试窗口图标
- 优化上一次配置运行和调试功能
- 删除对断点调试程序必须安装win32api的限制要求
- 添加项目菜单系列图标
- 添加清理项目和归档项目2个功能
- 修复复制项目文件和文档关闭时文本控件实例已经被删除的BUG
- 支持文件打开方式打开项目文件
- 断点调试支持异常断点
- 调整代码目录结构,将调试模块移至debugger文件夹中
- 更换选项设置箭头图标
- 优化导入文件全部选择和全部取消的功能
- 优化文件外部更改时告警,不重复告警
- 优化程序运行参数设置,保存历史参数列表,并能设置是否启用参数
- 添加文件属性,项目属性,和文件夹属性功能页面
- 断点调试交互页面支持按回车键执行命令
- 项目属性添加了引用项目页面
- 优化处理一些选项设置和窗口名称的中文名存储问题
- Web浏览器界面添加各个按钮的鼠标提示说明
- 文件打开方式界面调整编辑器先后顺序,将默认编辑器放在第一位
- 所有打开文件类型名称在中文环境时显示中文名称
- 修改所有文件类型编辑器模板名称
- 修复文件属性页路径太长导致控件被隐藏的BUG
- 添加边界线宽度以及默认新建文档类型设置
- 文件打开方式添加已文件名或文件扩展名方式打开,并修改项目文件项图标
- 添加shell文件和web浏览器图标- 支持当前行高亮和换行符模式设置
- 添加LINUX支持web浏览器功能
- 修复LINUX系统下解释器搜索路径页面flatmenu显示导致界面卡死的问题
- 修复删除文件模板时模板显示错位的问题
- 优化模板文件在切换中英文加载为空的问题
- 修复重启调试进程无法输出的BUG- 更新智能提示数据库时同时更新状态栏状态显示，并且在程序退出停止分析数据库时，不在状态栏显示
- 优化调试运行时启动目录不存在时的错误提示
- 支持解释器路径包含中文路径调试和运行
- 添加项目设置运行配置列表功能
- 支持运行配置启动文件，程序参数，解释器参数，PYTHONPATH，解释器等
- 修复解释器不支持中文路径的BUG,并弹出提示警告
- 添加解释器基本设置选项
- 支持软件调试模式切换中英文
- 调整调试窗口,将输出窗口移到调试主窗口中
- 运行项目时默认把项目路径添加到PYTHONPATH
- 支持隐藏并显示搜索窗口和内建解释器窗口
- 断点调试支持添加监视功能
- 在解释器基本选项中添加显示内建解释器窗口设置

Version 1.1.4 -------------2018-10-30
- 修复解释器智能分析无法导入wx模块的BUG
- 当添加解释器时新增是否自动创建智能提示数据库选项设置
- 新增解释器智能数据库更新间隔选项
- 修复linux系统下粘贴功能引起的剪贴板重复打开的BUG
- 修复解释器配置环境变量修改时,无法保存修改的BUG
- 优化调试和运行窗口关闭按钮事件
- 调试模式时显示日志窗口
- 加载解释器智能提示数据库时加载内建模块列表
- 新增打开项目时是否加装文件夹展开状态选项
- 添加对c/c++语言的注释模板支持
- 调试运行输出窗口右键菜单添加查找和导出文本功能
- 更改默认文本模板名称Any File为All Files
- python2和3断点调试支持重定向输入,并且输入字符显示蓝色
- 断点调试窗口支持标准错误输出为红色,标准输出显示为黑色
- 重定向输入按取消按钮时模拟键盘中断
- 修复文件属性资源页文件路径过长的问题
- 工程和资源视图添加工具栏
- 工程导入文件时记住选择的过滤文件类型
- 查看菜单支持全屏显示以及关闭全屏显示
- 文档右键菜单支持最大化和恢复文档窗口
- 优化停靠窗口样式,支持aui风格停靠窗口样式,允许关闭和最小化停靠窗口
- 支持文档主题设置，选项卡文档方向设置等
- 支持恢复默认窗口布局
- 程序退出时保存窗体布局，并在下一次启动时加载上一次的窗体布局
- 在其他选项里面添加窗口设置
- 修复winxp运行的一个BUG,并全面支持windows xp和国产深度操作系统运行
- 优化解释权pip包安装，安装完成后检查包是否安装成功
- 优化py3获取pip路径的方法,使用pip3代替pip名称
- 窗口菜单在文档数据超过限制后显示更多窗口项
- 支持同时打开多个文档
- 软件启动时优化历史项目加载效率,启动时不加载项目文档,只加载上一次打开的项目文档
- 修复转到定义无法定位到行的BUG
- 设置文档选项卡背景色为白色
- 更改项目文件名时同时更新大纲视图
- 大纲视图支持按类型排序
- 大纲视图添加显示行号,函数参数,以类的基类等选项设置
- 添加中文的每日提示支持
- 支持软件安装在中文路径
- 解释器窗口支持上下键切换历史命令
- pip支持安装包时选择最优源
- 初步支持加载插件扩展
- 支持所有语言的注释代码功能
- 适应插件开发模式,调整所有menu ids生成方式


Version 1.1.5 -------------2019-07-31
- 全新改版的UI界面
- 支持更换UI皮肤
- 可选几种语法主题
- 支持项目设置为Windows项目


Version 1.1.6 -------------2019-8-19
- 优化了代码渲染算法引擎,大大加快了渲染速度
- 修复了在工具首选项设置字体大小,系统内置关键字大小没变的BUG
- 优化历史文件列表显示,并修复历史文件列表超过限制无法添加新文件的问题
- 修复了c语言代码块注释渲染的BUG
- 发布了Linux1.1.6安装包
- 简化反馈功能,解决被360杀毒主程序隔离的问题
- 修复调式输出窗口右键菜单多次弹出的BUG
- 重新构建了内建模块的智能数据库文件
- 修复调式输出窗口关闭后无法还原编辑器窗口的BUG
- 丰富的智能提示
- 支持回车键代码自动缩进
- 修复输出文本导出文件的BUG
- 设置调式窗口输出每行最大字符数,超过字符数则分行输出
- 调式支持程序输入,对输入进行了处理
- tab键自动完成单词
- 语法解析支持连等表达式
- 支持鼠标悬停在文本上显示模块或函数提示文档信息
- 添加了IDLE Dark语法主题


Version 1.1.7 -------------2019-8-19
- 语法解析支持解析return表达式
- 优化self语句解析算法
- 优化tab键缩进算法
- 优化智能提示,能够显示更多模块成员
- 修复代码渲染文件过大时崩溃的BUG
- 帮助菜单添加Turtle Demo项,可以展示Turtle范例供新手学习
- toolbar支持分割线
- 修复工具菜单打开解释器的BUG
- 修复命令行参数设置对话框无法打开启动目录的BUG
- 修复智能提示导入赋值成员属性时候的BUG
- 修复打开文档失败时重复销毁文档框架的问题
- 智能提示支持显示导入模块,并定位时会打开模块的路径
- 智能提示会重新分析未完成解析导入的模块
- 支持断点调试,包括查看堆栈信息,监视断点,交互以及查看断点列表
- 删减了PIL模块不必要的加载插件,加快了软件启动速度
- 添加强制更新功能
- 软件启动时添加欢迎界面
- 允许设置断点
- 检查混合行尾
- 由于tkinter有tab键必须显示8个字符宽的BUG,故去除了和tab设置相关的选项和菜单


Version 1.1.8 -------------2019-9-12
- 调式模式时添加日志窗口
- 查找文本时取出文本的换行符,只取第一行文本
- 支持等比例缩放整个IDE窗口
- 添加Appearence面板
- 添加Outline面板
- 支持是否使用自定义菜单栏
- 修复Python2检查文件开头申明编码错误的BUG
- 项目视图item右键菜单发送消息以支持插件
- 屏蔽了默认绑定的F10,修复了F10快捷键断点调式的BUG
- 实现了图片的放大缩小
- 修复调试执行命令错误的BUG
- 修复智能提示某些测试模块和包无法找到引起的问题
- 修复linux下无法杀掉进程的BUG
- 优化了项目向导界面布局
- 支持用户开发自定义插件,以及插件管理
- 新建了pypi插件,支持一键式生成zip包并且可以发布到本地或者PyPI
- 新建Turtle Demo插件将原来帮助菜单的Turtle Demo项移至插件中加载
- 添加了插件管理器,并且支持下载,安装,启用以及禁止插件
- 添加了Pip包管理插件,可以从PyPI服务器上下载,搜索以及更新包
- 允许发布本地插件和上传到服务器,并能从服务器上下载插件
- 支持更新插件以及检查插件更新
- 优化解释器配置界面pip安装和卸载包


Version 1.1.9 -------------2019-10-29
- 将外观面板移至环境栏中
- 添加插件配置面板
- 项目解析器版本过期时弹出警告
- 新建pyinstaller插件并要求软件必须是1.1.9
- 更新了项目解析器版本,优化了删除项目
- 添加了文本自动缩进以及智能提示的设置选项
- 添加输出以及文件视图图标
- pypi插件升级到1.1版本
- 修复安装本地插件的BUG
- 根据输出来源来显示相应的日志
- 修复打开文件检测编码错误的BUG,python文件改为优先使用声明的编码
- 更新插件时检测插件要求的程序的最低版本
- 新建项目向导导入文件后设置项目启动文件


Version 1.2.0 -------------2019-11-27
- 优化解释器加载,未从注册表找到解释器的话接着从环境变量中查找解释器路径
- 修复程序参数分割的BUG
- 修复pyinstaller在linux下面的路径问题
- 更新帮助文档
- 调试模式时显示插件安装次数
- 修复智能提示输入混乱错误的BUG
- 打开文件后发送事件消息供插件处理
- 修复文件视图无法打开外部文件的BUG
- python解释器窗口改成shell窗口
- shell窗口模拟python解释器交互，并在后端进程执行并显示输出信息
- 优化智能提示from xx import样式的提示信息
- 添加shelleditor插件
- 在打开文件时如果不支持改文件扩展则去插件服务器上查找是否有该文件类型的插件
- 添加文件视图配置面板
- 支持添加异常断点
- 修复重命名文件夹以及移除项目文件夹的BUG
- 精简安装包大小,删除解释器内建成员数据库改为在程序启动时自动生成解释器内建成员数据库
- 更新翻译脚本,使用python3翻译工具pybabel.exe来生成pot文件,支持utf-8文件编码
- 日志窗口支持打印debug日志


Version 1.2.1 -------------2020-1-3
- 优化项目文件和文件夹重命名
- 发布gittool插件,支持clone,commit,checkout项目和代码
- 修复shell窗口内建解释器执行python命令的BUG
- 自动生成项目代码智能提示数据库
- 添加django插件,支持一键式转换django项目
- shell窗口支持输入
- 添加项目文件过滤器
- 支持刷新项目文件夹下的文件并添加到项目文件中
- 优化解释器加载,在注册表和环境变量中都去加载解释器
- 添加了自动完成插件,使用增强版智能提示功能可以边输入或边退格边提示
- 优化了智能提示以及修复一些BUG
- 支持文本自动插入成对的符号,如引号,三引号,括号等
- 检查插件是否付费
- 添加调试/运行配置面板
- 显示插件安装次数
- 支持设置调试标准输出,错误以及输入文本颜色
- 优化语法解析程序,删除不存在的模块智能提示数据库文件
- 支持注册,登录以及找回密码功能
- 添加启动时自动登录,并且在标题栏上显示登录账户信息功能,暂时不支持自动登录
- 修复调试器启动失败导致debugger视图无法删除的BUG
- 调试器运行时默认不允许编辑代码文件
- 优化了代码智能解析线程,设置为后台线程,防止程序退出时卡死
- 本地存储数据库添加了token字段,版本从1.0.2更新至1.0.3
- 修改初次安装设置默认显示工具栏
- 优化调试器监视显示监视值类型
- 调试器运行时设置是否鼠标悬停时显示监视文本的内存值
- 修复断点调试经常报KeyError的BUG

Version 1.2.2 -------------2020-2-25
- 修复项目新建文件夹/文件/包的BUG
- 安装插件时检查插件是否需要登录
- 全屏时双击编辑器窗口不允许最大化或恢复窗口
- 添加tomorrow风格的语法主题插件
- 添加对xml,html,css,javascript语言的语法高亮支持
- 修复python脚本对definition元素的语法高亮
- 修复linux下面解释器版本3.6时无法安装插件的BUG
- 更新pypi插件,发布插件到服务器需要注册并登陆
- 添加webbrowser插件,支持回退,前进,放大,缩小网页等操作,嵌入内部web浏览器到IDE
- 修复程序线程错误定位源码行数错误的BUG
- 新建文件对话框文件类型过多时显示滚动条,并使选中项可见
- 插入成双的符号,并将光标置于一对符号的中间
- 支持以打开方式打开项目文件
- 语言Lexer添加返回所有注释方式列表以及默认注释方式
- 插件管理器添加是否允许插件卸载的功能
- 注释模板添加Licence变量
- 修复添加解释器时解释器路径不存在导致添加不进去的BUG
- 支持插件区分操作系统不同版本
- 修复linux深度系统打开文件管理器的错误
- 优化pip安装virtualenv工具,通过配置文件使用国内源来安装工具
- 插件添加disabled属性,支持禁止安装插件
- 修复linux打开对话框错误_tkinter.TclError: grab failed: window not viewable
- 修改python测试用例模板


Version 1.2.3 -------------2020-4-10
- 添加起始页,支持在起始页创建,打开项目,以及显示历史项目列表,显示帮助,资讯信息以及学习教程
- 添加快捷键绑定自定义配置
- 制作了在线帮助文档
- 区分历史文件和历史项目列表,在起始页显示历史项目列表
- 支持发布插件区分操作系统不同的版本
- 正式版本添加注册和登录功能
- 设置url连接超时时间,防止程序长时间卡死
- 切换ui主题时发送ui切换主题消息
- 去掉启动检查版本更新的设置
- 支持并优化输出颜色的修改应用到所有输出窗口
- 修复linux操作配置文件的BUG
- 优化插件更新机制
- 优化PipManager插件包更新方式,更快捷方便
- 修复项目文件重复关闭多次跳出提示对话框的BUG
- IDE启动时自动安装OpenWebBrowser插件
- 支持发布开发版本(内测版本),和正式版本区别,并在检查ide更新时传递是否是开发版本的参数
- 安装新版本插件后删除旧版本的插件egg文件
- 修复chardet模块读取空文件编码为gb2312的BUG
- 优化了一些插件和软件的性能,加速了软件启动的速度
- 修复新建虚拟解释器的BUG
- 显示项目文件的路径tooltip信息
- 修复CEF控件焦点导致鼠标离开后text控件无法捕获键盘输入的BUG
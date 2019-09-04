# -*- coding: utf-8 -*-
from noval.constants import *
APPLICATION_NAME = "NovalIDE"
DEBUG_APPLICATION_NAME = APPLICATION_NAME + "Debug"

PROJECT_SHORT_EXTENSION = "nov"
PROJECT_EXTENSION = "." + PROJECT_SHORT_EXTENSION

DEFAUT_CONTRL_PAD_X = 10
DEFAUT_CONTRL_PAD_Y = 10

DEFAUT_HALF_CONTRL_PAD_X = 5
DEFAUT_HALF_CONTRL_PAD_Y = 5

UPDATE_ONCE_STARTUP = 0
UPDATE_ONCE_DAY = 1
UPDATE_ONCE_WEEK = 2
UPDATE_ONCE_MONTH = 3
NEVER_UPDATE_ONCE = 4

TEMPLATE_FILE_NAME = "template.xml"
USER_CACHE_DIR = "cache"
CHECK_UPDATE_ATSTARTUP_KEY = "CheckUpdateAtStartup"
DEFAULT_FILE_ENCODING_KEY = "DefaultFileEncoding"
REMBER_FILE_KEY = "RemberFile"
DEFAULT_DOCUMENT_TYPE_KEY = "DefaultDocumentType"
EDITOR_FONT_FAMILY_KEY =  "EditorFontFamily"
EDITOR_FONT_SIZE_KEY = "EditorFontSize"
IO_FONT_FAMILY_KEY =  "IoFontFamily"
SYNTAX_THEME_KEY = "SyntaxThemeName"
FRAME_MAXIMIZED_KEY = "MDIFrameMaximized"
#MDIFrame key表示主界面的坐标以及宽高
FRAME_TOP_LOC_KEY = "MDIFrameTopLoc"
FRAME_LEFT_LOC_KEY = "MDIFrameLeftLoc"
FRAME_WIDTH_KEY = "MDIFrameWidth"
FRAME_HEIGHT_KEY = "MDIFrameHeight"

FRAME_VIEW_VISIBLE_KEY = "%sViewVisible"
RECENT_FILES_KEY = "RecentFiles"
CURRENT_PROJECT_KEY = "ProjectCurrent"
PROJECT_DOCS_SAVED_KEY = "IsProjectSaveDocs"
PROJECT_SAVE_DOCS_KEY  = "ProjectSavedDocs"
ENABLE_MRU_KEY = "EnableMRU"
MRU_LENGTH_KEY = "MRULength"
LANGUANGE_ID_KEY = "LanguageId"


DEFAULT_FONT_FAMILY = "Courier New"
DEFAULT_FONT_SIZE = 11

DEFAULT_SYNTAX_THEME = "Default Light" 

DEFAULT_PLUGINS = ("noval.plugins.fileview.FileViewLoader","noval.find.findresult.FindResultsviewLoader",\
                   "noval.plugins.base_ui_themes.BaseUIThemeLoader","noval.plugins.clean_ui_themes.CleanUIThemeLoader",\
                   "noval.plugins.paren_matcher.ParenMatcherPluginLoader","noval.plugins.printer.FilePrinterPluginLoader",\
                    "noval.plugins.about.AboutLoader","noval.plugins.update.UpdateLoader")


NORMAL_MENU_ITEM_KIND = 0
SUB_MENU_ITEM_KIND = 1
CHECK_MENU_ITEM_KIND = 2
RADIO_MENU_ITEM_KIND = 3


OUTLINE_VIEW_NAME = "Outline"
FILE_VIEW_NAME = "Fileview"
PROJECT_VIEW_NAME = "Projectview"
SEARCH_RESULTS_VIEW_NAME = "SearchResults"
PYTHON_INTERPRETER_VIEW_NAME = "PythonInterpreter"

PROJECT_NAMESPACE_URL = "noval"

TREE_VIEW_FONT = "TreeviewFont"
TREE_VIEW_BOLD_FONT = "TreeviewBoldFont"

#默认历史文件个数
DEFAULT_MRU_FILE_NUM = 9
#最大历史文件个数
MAX_MRU_FILE_LIMIT = 20

#状态栏显示的标签名称,行列以及文件编码
STATUS_BAR_LABEL_LINE = "line"
STATUS_BAR_LABEL_COL = "column"
STATUS_BAR_LABEL_ENCODING = "encoding"

#工具栏排列在第一行的位置
DEFAULT_TOOL_BAR_ROW = 0
#工具栏排列在第三行的位置
DEFAULT_STATUS_BAR_ROW = 3
#主框架排列在第二行的位置
DEFAULT_MAIN_FRAME_ROW = 1


WINDOWS_UI_THEME_NAME = "Windows"
CLAM_UI_THEME_NAME = "clam"
ENHANCED_CLAM_UI_THEME_NAME = "Enhanced Clam"
AQUA_UI_THEME_NAME = "aqua"
XPNATIVE_UI_THEME_NAME = "xpnative"


##空文件夹下面建立一个虚拟空文件的内容,这个虚拟文件是隐藏的
DUMMY_NODE_TEXT = "..."


PROJECT_ADD_COMMAND_NAME            = "add"
PROJECT_ADD_PROGRESS_COMMAND_NAME   = "progress_add"

#the first 2 line no of python file to place encoding declare
ENCODING_DECLARE_LINE_NUM = 2

PYTHON_PATH_NAME = 'PYTHONPATH'
NOT_IN_ANY_PROJECT = "Not in any Project"

DEFAULT_EDGE_GUIDE_WIDTH = 78

EOL_CR = 0
EOL_LF = 1
EOL_CRLF = 2

EOL_DIC = {
    EOL_CR:"\r",
    EOL_LF:"\n",
    EOL_CRLF:"\r\n"
}

INTERACTCONSOLE_TAB_NAME = "InteractConsole"
BREAKPOINTS_TAB_NAME = "Breakpoints"
STACKFRAME_TAB_NAME = "StackFrame"
WATCH_TAB_NAME = "Watchs"
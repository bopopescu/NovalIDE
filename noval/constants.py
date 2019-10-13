# -*- coding: utf-8 -*-
#-------------------------------------------------------------------------------
# Name:        constants.py
# Purpose:
#
# Author:      wukan
#
# Created:     2019-01-16
# Copyright:   (c) wukan 2019
# Licence:     GPL-3.0
#-------------------------------------------------------------------------------
from noval import NewId


# File Menu IDs

ID_NEW                          = NewId()
ID_OPEN                         = NewId()
ID_CLOSE                        = NewId()
ID_CLOSE_ALL                    = NewId()
ID_SAVE                         = NewId()
ID_SAVEAS                       = NewId()
ID_SAVEALL                      = NewId()
ID_PRINT                        = NewId()
ID_EXIT                         = NewId()
    
    
# Edit Menu IDs 
    
ID_UNDO                         = NewId()
ID_REDO                         = NewId()
ID_CUT                          = NewId()
ID_COPY                         = NewId()
ID_PASTE                        = NewId()
ID_CLEAR                        = NewId()
ID_SELECTALL                    = NewId()
    
ID_FIND                         = NewId()            # for bringing up Find dialog box
ID_FIND_PREVIOUS                = NewId()   # for doing Find Next
ID_FIND_NEXT                    = NewId()       # for doing Find Prev
ID_REPLACE                      = NewId()         # for bringing up Replace dialog box
ID_GOTO_LINE                    = NewId()       # for bringing up Goto dialog box
    
ID_FINDFILE                     = NewId()        # for bringing up Find in File dialog box
ID_FINDALL                      = NewId()         # for bringing up Find All dialog box
ID_FINDDIR                      = NewId()         # for bringing up Find Dir dialog box
    
ID_INSERT                       = NewId()
ID_INSERT_DATETIME              = NewId()
ID_INSERT_COMMENT_TEMPLATE      = NewId()
ID_INSERT_FILE_CONTENT          = NewId()
ID_INSERT_DECLARE_ENCODING      = NewId()
    
ID_ADVANCE                      = NewId()
ID_UPPERCASE                    = NewId()
ID_LOWERCASE                    = NewId()
ID_FIRST_UPPERCASE              = NewId()
ID_COPY_LINE                    = NewId()
ID_CUT_LINE                     = NewId()
ID_DELETE_LINE                  = NewId()
ID_CLONE_LINE                   = NewId()
ID_TAB_SPACE                    = NewId()
ID_SPACE_TAB                    = NewId()
    
ID_GOTO_DEFINITION              = NewId()
ID_WORD_LIST                    = NewId()
ID_AUTO_COMPLETE                = NewId()
ID_LIST_MEMBERS                 = NewId()
    
# View Menu IDs 
ID_VIEW_TOOLBAR                 = NewId()
ID_VIEW_STATUSBAR               = NewId()
ID_VIEW_APPLICAITON_LOOK        = NewId()
    
ID_OUTLINE_SORT                 = NewId()
ID_SORT_BY_LINE                 = NewId()
ID_SORT_BY_NAME                 = NewId()
ID_SORT_BY_NONE                 = NewId()
ID_SORT_BY_TYPE                 = NewId()
    
    
ID_TEXT                         = NewId()
ID_VIEW_WHITESPACE              = NewId()
ID_VIEW_EOL                     = NewId()
ID_VIEW_INDENTATION_GUIDES      = NewId()
ID_VIEW_RIGHT_EDGE              = NewId()
ID_VIEW_LINE_NUMBERS            = NewId()
    
ID_ZOOM                         = NewId()
ID_ZOOM_NORMAL                  = NewId()
ID_ZOOM_IN                      = NewId()
ID_ZOOM_OUT                     = NewId()

ID_NEXT_POS                     = NewId()
ID_PRE_POS                      = NewId()
ID_SHOW_FULLSCREEN              = NewId()

# Format Menu IDs
ID_CLEAN_WHITESPACE             = NewId()
ID_COMMENT_LINES                = NewId()
ID_UNCOMMENT_LINES              = NewId()
ID_INDENT_LINES                 = NewId()
ID_DEDENT_LINES                 = NewId()
ID_USE_TABS                     = NewId()
ID_SET_INDENT_WIDTH             = NewId()

ID_EOL_MODE                     = NewId()
ID_EOL_MAC                      = NewId()
ID_EOL_UNIX                     = NewId()
ID_EOL_WIN                      = NewId()

# Project Menu IDs
ID_NEW_PROJECT                  = NewId()
ID_OPEN_PROJECT                 = NewId()
ID_SAVE_PROJECT                 = NewId()
ID_CLOSE_PROJECT                = NewId()
ID_DELETE_PROJECT               = NewId()
ID_CLEAN_PROJECT                = NewId()
ID_ARCHIVE_PROJECT              = NewId()
ID_ADD_FOLDER                   = NewId()
ID_IMPORT_FILES                 = NewId()
ID_ADD_NEW_FILE                 = NewId()
ID_ADD_PACKAGE_FOLDER           = NewId()
ID_ADD_FILES_TO_PROJECT         = NewId()
ID_ADD_CURRENT_FILE_TO_PROJECT  = NewId()
ID_ADD_DIR_FILES_TO_PROJECT     = NewId()
ID_PROPERTIES                   = NewId()

#project popup Menu IDs
ID_OPEN_SELECTION               = NewId()
ID_OPEN_SELECTION_WITH          = NewId()
ID_REMOVE_FROM_PROJECT          = NewId()
ID_RENAME                       = NewId()
ID_SET_PROJECT_STARTUP_FILE     = NewId()
ID_OPEN_FOLDER_PATH             = NewId()
ID_COPY_PATH                    = NewId()
ID_OPEN_TERMINAL_PATH           = NewId()

# Run Menu IDs
ID_RUN                          = NewId()
ID_DEBUG                        = NewId()
ID_SET_EXCEPTION_BREAKPOINT     = NewId()
ID_STEP_INTO                    = NewId()
ID_STEP_CONTINUE                = NewId()
ID_STEP_OUT                     = NewId()
ID_STEP_NEXT                    = NewId()

ID_EXECUTE_CODE                 = NewId()
ID_BREAK_INTO_DEBUGGER          = NewId()
ID_RESTART_DEBUGGER             = NewId()
ID_QUICK_ADD_WATCH              = NewId()
ID_ADD_WATCH                    = NewId()
ID_ADD_TO_WATCH                 = NewId()
ID_TERMINATE_DEBUGGER           = NewId()


ID_CHECK_SYNTAX                 = NewId()
ID_SET_PARAMETER_ENVIRONMENT    = NewId()
ID_RUN_LAST                     = NewId()
ID_DEBUG_LAST                   = NewId()

ID_TOGGLE_BREAKPOINT            = NewId()
ID_CLEAR_ALL_BREAKPOINTS        = NewId()
ID_START_WITHOUT_DEBUG          = NewId()

# Tools Menu IDs
ID_OPEN_TERMINAL                = NewId()
ID_UNITTEST                     = NewId()
ID_OPEN_INTERPRETER             = NewId()
ID_OPEN_BROWSER                 = NewId()
ID_PLUGIN                       = NewId()
ID_PREFERENCES                  = NewId()
    
    
# Help Menu IDs 
ID_OPEN_PYTHON_HELP             = NewId()
ID_TIPS_DAY                     = NewId()
ID_CHECK_UPDATE                 = NewId()
ID_GOTO_OFFICIAL_WEB            = NewId()
ID_GOTO_PYTHON_WEB              = NewId()
ID_FEEDBACK                     = NewId()
ID_ABOUT                        = NewId()
    
    
#Document popup Menu IDs    
ID_NEW_MODULE                   = NewId()
ID_SAVE_DOCUMENT                = NewId()
ID_SAVE_AS_DOCUMENT             = NewId()
ID_CLOSE_DOCUMENT               = NewId()
ID_CLOSE_ALL_WITHOUT            = NewId()
ID_OPEN_DOCUMENT_DIRECTORY      = NewId()
ID_OPEN_TERMINAL_DIRECTORY      = NewId()
ID_COPY_DOCUMENT_PATH           = NewId()
ID_COPY_DOCUMENT_NAME           = NewId()
ID_COPY_MODULE_NAME             = NewId()
ID_MAXIMIZE_EDITOR_WINDOW       = NewId()
ID_RESTORE_EDITOR_WINDOW        = NewId()


#toolbar combo interpreter list
ID_COMBO_INTERPRETERS = NewId()
ID_OUTLINE_SYNCTREE = NewId()


ID_REFRESH_PATH = NewId()
ID_OPEN_DIR_PATH = NewId()
ID_OPEN_CMD_PATH = NewId()
ID_COPY_FULLPATH = NewId()
ID_ADD_FOLDER = NewId()
ID_CREATE_NEW_FILE = NewId()


ID_OK                       = NewId()
ID_CANCEL                   = NewId()

ID_YES                      = NewId()
ID_NO                       = NewId()
ID_YESTOALL                 = NewId()
ID_NOTOALL                  = NewId()


#项目视图右键菜单发送给插件的消息,插件接收消息在消息函数里面就可以添加自定义菜单项了
PROJECTVIEW_POPUP_FOLDER_MENU_EVT = 'EvtPopupProjectFolderMenu'
PROJECTVIEW_POPUP_FILE_MENU_EVT = 'EvtPopupProjectFileMenu'
PROJECTVIEW_POPUP_ROOT_MENU_EVT = 'EvtPopupProjectRootMenu'

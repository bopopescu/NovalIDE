import wx
import wx.lib.pydocview


# File Menu IDs

ID_NEW                          = wx.ID_NEW
ID_OPEN                         = wx.ID_OPEN
ID_CLOSE                        = wx.ID_CLOSE
ID_CLOSE_ALL                    = wx.ID_CLOSE_ALL
ID_SAVE                         = wx.ID_SAVE
ID_SAVEAS                       = wx.ID_SAVEAS
ID_SAVEALL                      = wx.lib.pydocview.SAVEALL_ID
ID_PRINT                        = wx.ID_PRINT
ID_PRINT_PREVIEW                = wx.ID_PREVIEW
ID_PRINT_SETUP                  = wx.ID_PRINT_SETUP
ID_EXIT                         = wx.ID_EXIT
        
ID_MRU_FILE1                    = wx.NewId()
ID_MRU_FILE2                    = wx.NewId()
ID_MRU_FILE3                    = wx.NewId()
ID_MRU_FILE4                    = wx.NewId()
ID_MRU_FILE5                    = wx.NewId()
ID_MRU_FILE6                    = wx.NewId()
ID_MRU_FILE7                    = wx.NewId()
ID_MRU_FILE8                    = wx.NewId()
ID_MRU_FILE9                    = wx.NewId()
ID_MRU_FILE10                   = wx.NewId()
ID_MRU_FILE11                   = wx.NewId()
ID_MRU_FILE12                   = wx.NewId()
ID_MRU_FILE13                   = wx.NewId()
ID_MRU_FILE14                   = wx.NewId()
ID_MRU_FILE15                   = wx.NewId()
ID_MRU_FILE16                   = wx.NewId()
ID_MRU_FILE17                   = wx.NewId()
ID_MRU_FILE18                   = wx.NewId()
ID_MRU_FILE19                   = wx.NewId()
ID_MRU_FILE20                   = wx.NewId()
    
    
# Edit Menu IDs 
    
ID_UNDO                         = wx.ID_UNDO
ID_REDO                         = wx.ID_REDO
ID_CUT                          = wx.ID_CUT
ID_COPY                         = wx.ID_COPY
ID_PASTE                        = wx.ID_PASTE
ID_CLEAR                        = wx.ID_CLEAR
ID_SELECTALL                    = wx.ID_SELECTALL
    
ID_FIND                         = wx.ID_FIND            # for bringing up Find dialog box
ID_FIND_PREVIOUS                = wx.NewId()   # for doing Find Next
ID_FIND_NEXT                    = wx.NewId()       # for doing Find Prev
ID_REPLACE                      = wx.ID_REPLACE         # for bringing up Replace dialog box
ID_GOTO_LINE                    = wx.NewId()       # for bringing up Goto dialog box
    
ID_FINDFILE                     = wx.NewId()        # for bringing up Find in File dialog box
ID_FINDALL                      = wx.NewId()         # for bringing up Find All dialog box
ID_FINDDIR                      = wx.NewId()         # for bringing up Find Dir dialog box
    
    
ID_TOGGLE_MARKER                = wx.NewId()
ID_DELALL_MARKER                = wx.NewId()
ID_NEXT_MARKER                  = wx.NewId()
ID_PREV_MARKER                  = wx.NewId()
ID_BOOKMARKER                   = wx.NewId()
    
ID_INSERT_TEXT                  = wx.NewId()
ID_INSERT_DATETIME              = wx.NewId()
ID_INSERT_COMMENT_TEMPLATE      = wx.NewId()
ID_INSERT_FILE_CONTENT          = wx.NewId()
ID_INSERT_DECLARE_ENCODING      = wx.NewId()
    
ID_EDIT_ADVANCE                 = wx.NewId()
ID_UPPERCASE                    = wx.NewId()
ID_LOWERCASE                    = wx.NewId()
ID_TAB_SPACE                    =  wx.NewId()
ID_SPACE_TAB                    =  wx.NewId()
    
ID_GOTO_DEFINITION              = wx.NewId()
ID_WORD_LIST                    = wx.NewId()
ID_AUTO_COMPLETE                = wx.NewId()
ID_LIST_MEMBERS                 = wx.NewId()
    
# View Menu IDs 
ID_VIEW_TOOLBAR                 = wx.lib.pydocview.VIEW_TOOLBAR_ID
ID_VIEW_STATUSBAR               = wx.lib.pydocview.VIEW_STATUSBAR_ID
    
ID_SORT                         = wx.NewId()
ID_SORT_BY_LINE                 = wx.NewId()
ID_SORT_BY_NAME                 = wx.NewId()
ID_SORT_BY_NONE                 = wx.NewId()
ID_SORT_BY_TYPE                 = wx.NewId()
    
    
ID_TEXT                         = wx.NewId()
ID_VIEW_WHITESPACE              = wx.NewId()
ID_VIEW_EOL                     = wx.NewId()
ID_VIEW_INDENTATION_GUIDES      = wx.NewId()
ID_VIEW_RIGHT_EDGE              = wx.NewId()
ID_VIEW_LINE_NUMBERS            = wx.NewId()
    
ID_ZOOM                         = wx.NewId()
ID_ZOOM_NORMAL                  = wx.NewId()
ID_ZOOM_IN                      = wx.NewId()
ID_ZOOM_OUT                     = wx.NewId()
    
ID_FOLD                         = wx.NewId()
ID_ENABLE_FOLD                  = wx.NewId()
ID_FOLD_EXPAND                  = wx.NewId()
ID_FOLD_COLLAPSE                = wx.NewId()
ID_EXPAND_TOP                   = wx.NewId()
ID_COLLAPSE_TOP                 = wx.NewId()
ID_EXPAND_ALL                   = wx.NewId()
ID_COLLAPSE_ALL                 = wx.NewId()

ID_NEXT_POS                     = wx.NewId()
ID_PRE_POS                      = wx.NewId()
ID_SHOW_FULLSCREEN              = wx.NewId()

# Format Menu IDs
ID_CLEAN_WHITESPACE             = wx.NewId()
ID_COMMENT_LINES                = wx.NewId()
ID_UNCOMMENT_LINES              = wx.NewId()
ID_INDENT_LINES                 = wx.NewId()
ID_DEDENT_LINES                 = wx.NewId()
ID_USE_TABS                     = wx.NewId()
ID_SET_INDENT_WIDTH             = wx.NewId()

ID_EOL_MODE                     = wx.NewId()
ID_EOL_MAC                      = wx.NewId()
ID_EOL_UNIX                     = wx.NewId()
ID_EOL_WIN                      = wx.NewId()

# Project Menu IDs
ID_NEW_PROJECT                  = wx.NewId()
ID_OPEN_PROJECT                 = wx.NewId()
ID_SAVE_PROJECT                 = wx.NewId()
ID_CLOSE_PROJECT                = wx.NewId()
ID_DELETE_PROJECT               = wx.NewId()
ID_CLEAN_PROJECT                = wx.NewId()
ID_ARCHIVE_PROJECT              = wx.NewId()
ID_ADD_FOLDER                   = wx.NewId()
ID_IMPORT_FILES                 = wx.NewId()
ID_ADD_NEW_FILE                 = wx.NewId()
ID_ADD_PACKAGE_FOLDER           = wx.NewId()
ID_ADD_FILES_TO_PROJECT         = wx.NewId()
ID_ADD_CURRENT_FILE_TO_PROJECT  = wx.NewId()
ID_ADD_DIR_FILES_TO_PROJECT     = wx.NewId()
ID_PROJECT_PROPERTIES           = wx.NewId()
ID_OPEN_PROJECT_PATH            = wx.NewId()

#project popup Menu IDs
ID_START_DEBUG                  = wx.NewId()
ID_START_RUN                    = wx.NewId()
ID_OPEN_SELECTION               = wx.NewId()
ID_OPEN_SELECTION_WITH          = wx.NewId()
ID_REMOVE_FROM_PROJECT          = wx.NewId()
ID_SET_PROJECT_STARTUP_FILE     = wx.NewId()
ID_OPEN_FOLDER_PATH             = wx.NewId()
ID_COPY_PATH                    = wx.NewId()
ID_OPEN_TERMINAL_PATH           = wx.NewId()

# Run Menu IDs
ID_RUN                          = wx.NewId()
ID_DEBUG                        = wx.NewId()
ID_SET_EXCEPTION_BREAKPOINT     = wx.NewId()
ID_STEP_INTO                    = wx.NewId()
ID_STEP_CONTINUE                = wx.NewId()
ID_STEP_OUT                     = wx.NewId()
ID_STEP_NEXT                    = wx.NewId()

ID_BREAK_INTO_DEBUGGER          = wx.NewId()
ID_RESTART_DEBUGGER             = wx.NewId()
ID_QUICK_ADD_WATCH              = wx.NewId()
ID_ADD_WATCH                    = wx.NewId()
ID_ADD_TO_WATCH                 = wx.NewId()
ID_TERMINATE_DEBUGGER           = wx.NewId()


ID_CHECK_SYNTAX                 = wx.NewId()
ID_SET_PARAMETER_ENVIRONMENT    = wx.NewId()
ID_RUN_LAST                     = wx.NewId()
ID_DEBUG_LAST                   = wx.NewId()

ID_TOGGLE_BREAKPOINT            = wx.NewId()
ID_CLEAR_ALL_BREAKPOINTS        = wx.NewId()
ID_START_WITHOUT_DEBUG          = wx.NewId()

# Tools Menu IDs
ID_OPEN_TERMINAL                = wx.NewId()
ID_UNITTEST                     = wx.NewId()
ID_OPEN_INTERPRETER             = wx.NewId()
ID_OPEN_BROWSER                 = wx.NewId()
ID_PREFERENCES                  = wx.ID_PREFERENCES
    
# Window Menu IDs   
ID_ARRANGE_WINDOWS              = wx.lib.pydocview.WindowMenuService.ARRANGE_WINDOWS_ID
ID_SELECT_MORE_WINDOWS          = wx.lib.pydocview.WindowMenuService.SELECT_MORE_WINDOWS_ID
ID_SELECT_NEXT_WINDOW           = wx.lib.pydocview.WindowMenuService.SELECT_NEXT_WINDOW_ID
ID_SELECT_PREV_WINDOW           = wx.lib.pydocview.WindowMenuService.SELECT_PREV_WINDOW_ID
ID_CLOSE_CURRENT_WINDOW         = wx.lib.pydocview.WindowMenuService.CLOSE_CURRENT_WINDOW_ID
ID_RESTORE_WINDOW_LAYOUT        = wx.NewId()
    
    
# Help Menu IDs 
ID_OPEN_PYTHON_HELP             = wx.NewId()
ID_TIPS_DAY                     = wx.NewId()
ID_CHECK_UPDATE                 = wx.NewId()
ID_GOTO_OFFICIAL_WEB            = wx.NewId()
ID_GOTO_PYTHON_WEB              = wx.NewId()
ID_FEEDBACK                     = wx.NewId()
ID_ABOUT                        = wx.ID_ABOUT
    
    
#Document popup Menu IDs    
ID_NEW_MODULE                   = wx.NewId()
ID_SAVE_DOCUMENT                = wx.NewId()
ID_SAVE_AS_DOCUMENT             = wx.NewId()
ID_CLOSE_DOCUMENT               = wx.NewId()
ID_CLOSE_ALL_WITHOUT            = wx.NewId()
ID_OPEN_DOCUMENT_DIRECTORY      = wx.NewId()
ID_OPEN_TERMINAL_DIRECTORY      = wx.NewId()
ID_COPY_DOCUMENT_PATH           = wx.NewId()
ID_COPY_DOCUMENT_NAME           = wx.NewId()
ID_COPY_MODULE_NAME             = wx.NewId()
ID_MAXIMIZE_EDITOR_WINDOW       = wx.NewId()
ID_RESTORE_EDITOR_WINDOW        = wx.NewId()


#toolbar combo interpreter list
ID_COMBO_INTERPRETERS = wx.NewId()

_ = wx.GetTranslation


DEFAULT_PLUGINS = ("noval.tool.Feedback.FeedBack",)


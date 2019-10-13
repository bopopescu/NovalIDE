
OK = 0
UNKNOWN_ERROR = -1
PLUGIN_EGG_FILE_EXISTS = 1

ERROR_CODE_MESSAGES = {
    PLUGIN_EGG_FILE_EXISTS     : 'plugin version {version} has already exist,do you want to replace it',
    OK                         : '',
    UNKNOWN_ERROR             :'unkown error'
}

def GetCodeMessage(error_code):
    return ERROR_CODE_MESSAGES.get(error_code,ERROR_CODE_MESSAGES[UNKNOWN_ERROR])

OK = 0
UNKNOWN_ERROR = -1
PLUGIN_EGG_FILE_EXISTS = 1
PLUGIN_EGG_FILE_NOT_FOUND = 2
PLUGIN_VERSION_NOT_FOUND = 3

ERROR_CODE_MESSAGES = {
    PLUGIN_EGG_FILE_EXISTS     : 'plugin \'{name}\' version {version} has already exist,do you want to replace it',
    OK                         : '',
    PLUGIN_VERSION_NOT_FOUND   :'plugin \'{name}\' version {version} was not found',
    UNKNOWN_ERROR             :'unkown error'
}

def GetCodeMessage(error_code):
    return ERROR_CODE_MESSAGES.get(error_code,ERROR_CODE_MESSAGES[UNKNOWN_ERROR])

OK = 0
UNKNOWN_ERROR = -1
PLUGIN_EGG_FILE_EXISTS = 1
PLUGIN_EGG_FILE_NOT_FOUND = 2
PLUGIN_VERSION_NOT_FOUND = 3
EMAIL_NOT_EXIST = 4
PASSWORD_NOT_CORRECT = 5
INVALID_ACTIVATE_URL = 6
ERROR_VERIFICATION_CODE = 7
PROGRAM_FILE_NOT_EXIST = 8
USER_ALREADY_REGISTERED = 9
USER_NOT_EXIST       = 10
INVALID_LOGIN_TOKEN  = 11

ERROR_CODE_MESSAGES = {
    PLUGIN_EGG_FILE_EXISTS     : 'plugin \'{name}\' version {version} has already exist,do you want to replace it',
    OK                         : '',
    PLUGIN_VERSION_NOT_FOUND   :'plugin \'{name}\' version {version} was not found',
    EMAIL_NOT_EXIST            :'the email is not exist',
    PASSWORD_NOT_CORRECT       :'password is not correct',
    INVALID_ACTIVATE_URL       :'invalid activate url',
    ERROR_VERIFICATION_CODE    :'verification code is unknown',
    PROGRAM_FILE_NOT_EXIST     :'program file is not exist,you need to intall it from source code',
    USER_ALREADY_REGISTERED    :'user already registerd',
    USER_NOT_EXIST             :'user is not exist',
    INVALID_LOGIN_TOKEN        :'invalid login token',
    UNKNOWN_ERROR              :'unkown error'
}

def GetCodeMessage(error_code):
    return ERROR_CODE_MESSAGES.get(error_code,ERROR_CODE_MESSAGES[UNKNOWN_ERROR])
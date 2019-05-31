from noval import GetApp
import sys
import os
import noval.consts as consts
import noval.ui_utils as ui_utils

def get_tk_version_str():
    tkVer = GetApp().call('info', 'patchlevel')
    return tkVer
    
def get_python_version_string():
    version_info = sys.version_info
    result = ".".join(map(str, version_info[:3]))
    if version_info[3] != "final":
        result += "-" + version_info[3]
    result += " (" + ("64" if sys.maxsize > 2 ** 32 else "32") + " bit)\n"
    return result
    
def update_pythonpath_env(env,pythonpath):
    if type(pythonpath) == list:
        pathstr = os.pathsep.join(pythonpath)
    else:
        pathstr = pythonpath
    env[consts.PYTHON_PATH_NAME] = env[consts.PYTHON_PATH_NAME] + os.pathsep + pathstr
    return env

def get_override_runparameter(run_parameter):
    interpreter = run_parameter.Interpreter
    environment = run_parameter.Environment
    environ = interpreter.Environ.GetEnviron()
    if consts.PYTHON_PATH_NAME in environ and environment is not None:
        environ = update_pythonpath_env(environ,environment.get(consts.PYTHON_PATH_NAME,''))
    environ = ui_utils.update_environment_with_overrides(environ)
    if len(environ) > 0:
        if environment is None:
            environment = environ
        else:
            environment.update(environ)
        #in windows and if is python3 interpreter ,shoud add 'SYSTEMROOT' Environment Variable
        #othersise it will raise progblem below when add a Environment Variable
        #Fatal Python error: failed to get random numbers to initialize Python
       # if sysutilslib.isWindows() and interpreter.IsV3():
        #    SYSTEMROOT_KEY = 'SYSTEMROOT'
         #   if not environment.has_key(SYSTEMROOT_KEY):
          #      environment[SYSTEMROOT_KEY] = os.environ[SYSTEMROOT_KEY]
    #add python path to env
    if len(interpreter.PythonPathList) > 0:
        environment = update_pythonpath_env(environment,interpreter.PythonPathList)
    if run_parameter.Environment == environment:
        return run_parameter
    else:
        save_interpreter = run_parameter.Interpreter
        run_parameter.Interpreter = None
        cp_run_parameter = copy.deepcopy(run_parameter)
        cp_run_parameter.Environment = environment
        run_parameter.Interpreter = save_interpreter
        return cp_run_parameter
    
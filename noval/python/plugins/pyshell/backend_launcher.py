# -*- coding: utf-8 -*-
from __future__ import print_function

"""
This file is run by CPythonProxy

(Why separate file for launching? I want to have clean global scope 
in toplevel __main__ module (because that's where user scripts run), but backend's global scope 
is far from clean. 
I could also do python -c "from backend import VM: VM().mainloop()", but looks like this 
gives relative __file__-s on imported modules.) 
"""

if __name__ == "__main__":
    # imports required by the backend itself
    import sys

    if not sys.version_info > (2, 7):
        print(
            "NovalIDE only supports Python 2.7 and later.\n"
            + "Choose another interpreter from Tools => Options => Interpreter",
            file=sys.stderr,
        )
        exit()

    import logging
    import os.path
    NOVAL_USER_DIR = os.environ["NOVAL_USER_DIR"]
    shell_path = os.path.normpath(os.path.join(NOVAL_USER_DIR,"noval/python/plugins/pyshell"))
    sys.path.append(shell_path)
    sys.path.append(os.path.normpath(os.path.join(NOVAL_USER_DIR,"noval/util")))
    # set up logging
    logger = logging.getLogger("novalide.backendrun.debug")
    logger.propagate = False
    logFormatter = logging.Formatter("%(levelname)s: %(message)s")
    BACKEND_LOG_PATH = os.environ["BACKEND_LOG_PATH"]
    file_handler = logging.FileHandler(
        os.path.join(BACKEND_LOG_PATH, "backend.log"), encoding="UTF-8", mode="w"
    )
    file_handler.setFormatter(logFormatter)
    file_handler.setLevel(logging.INFO)
    logger.addHandler(file_handler)

    # Don't litter user stderr with thonny logging
    # TODO: Can I somehow send the log to front-end's stderr?
    """
    stream_handler = logging.StreamHandler(stream=sys.stderr)
    stream_handler.setLevel(logging.INFO);
    stream_handler.setFormatter(logFormatter)
    logger.addHandler(stream_handler)
    """

    logger.setLevel(logging.INFO)
    if sys.version_info.major == 3:
        import faulthandler
        fault_out = open(os.path.join(BACKEND_LOG_PATH, "backend_faults.log"), mode="w")
        faulthandler.enable(fault_out)

    import backend3
    backend3.VM().mainloop()

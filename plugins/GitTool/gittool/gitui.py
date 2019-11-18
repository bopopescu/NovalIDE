from noval.python.project.viewer import *
import os
import tkinter as tk
from tkinter import ttk,messagebox
from noval import _
import noval.util.utils as utils
import noval.project.wizard as projectwizard
import threading
import noval.outputthread as outputthread
import subprocess
import noval.ui_base as ui_base
import noval.util.compat as compat

class CloneProgressDialog(ui_base.GenericProgressDialog):
    def __init__(self,parent):
        ui_base.GenericProgressDialog.__init__(self,parent,_("Clone project"),
                               mode="indeterminate",info=_("Please wait a minute for end clone...")
                                )
        self.KeepGoing = True
        
    def AppendMsg(self,msg):
        print (msg,'=================')
        if utils.is_py3_plus():
            msg = compat.ensure_string(msg)
        if not msg:
            return
        for message in msg.split('\r'):
            self.label_var.set(message.strip())

    def Pulse(self):
        self.mpb.start()
        
    def Cancel(self):
        self.mpb.stop()
        ui_base.GenericProgressDialog.Cancel(self)

class GitProjectNameLocationPage(BasePythonProjectNameLocationPage):

    def __init__(self,master,**kwargs):
        BasePythonProjectNameLocationPage.__init__(self,master,**kwargs)
        self.can_finish = False

class ImportFilesPage(projectwizard.BitmapTitledContainerWizardPage):
    def __init__(self,master):
        projectwizard.BitmapTitledContainerWizardPage.__init__(self,master,_("Import codes from Git Server"),_("Source Git Repository\nEnter the location of the source repository."),"python_logo.png")
        self.can_finish = True

    def CreateContent(self,content_frame,**kwargs):
        sizer_frame = ttk.Frame(content_frame)
        sizer_frame.grid(column=0, row=1, sticky="nsew")
        
        sizer_frame.columnconfigure(1, weight=1)

        ttk.Label(sizer_frame,text=_('Repository addr:')).grid(column=0, row=0, sticky="nsew",padx=(0,consts.DEFAUT_CONTRL_PAD_X),pady=(consts.DEFAUT_CONTRL_PAD_Y,0))
        self.addr_var = tk.StringVar()
        name_entry = ttk.Entry(sizer_frame,textvariable=self.addr_var)
        name_entry.grid(column=1, row=0, sticky="nsew",pady=(consts.DEFAUT_CONTRL_PAD_Y,0),padx=(0,consts.DEFAUT_CONTRL_PAD_X))

        ttk.Label(sizer_frame,text=_('Username:')).grid(column=0, row=1, sticky="nsew",padx=(0,consts.DEFAUT_CONTRL_PAD_X),pady=(consts.DEFAUT_CONTRL_PAD_Y,0))
        self.name_var = tk.StringVar()
        name_entry = ttk.Entry(sizer_frame,textvariable=self.name_var)
        name_entry.grid(column=1, row=1, sticky="nsew",pady=(consts.DEFAUT_CONTRL_PAD_Y,0),padx=(0,consts.DEFAUT_CONTRL_PAD_X))
        
        ttk.Label(sizer_frame,text=_('Password:')).grid(column=0, row=2, sticky="nsew",padx=(0,consts.DEFAUT_CONTRL_PAD_X),pady=(consts.DEFAUT_CONTRL_PAD_Y,0))
        self.password_var = tk.StringVar()
        password_entry = ttk.Entry(sizer_frame,textvariable=self.password_var,show='*')
        password_entry.grid(column=1, row=2, sticky="nsew",pady=(consts.DEFAUT_CONTRL_PAD_Y,0),padx=(0,consts.DEFAUT_CONTRL_PAD_X))
        
        self.store_secure_var = tk.BooleanVar(value=False)
        store_secure_btn = ttk.Checkbutton(sizer_frame,text=_('Store in Secure Store'),variable=self.store_secure_var)
        store_secure_btn.grid(column=0, row=3, sticky="nsew",columnspan=2,pady=consts.DEFAUT_CONTRL_PAD_Y)
        
        return sizer_frame
        
    def Validate(self):
        progress_dlg = CloneProgressDialog(self)
        self.CloneGitProject(progress_dlg)
        progress_dlg.Pulse()
        progress_dlg.ShowModal()
        return False

    def CloneGitProject(self,progress_dlg):
        t = threading.Thread(target=self.CloneProject,args=(progress_dlg,))
        t.start()
        
    def ExecCommandAndOutput(self,command,progress_dlg):
        #shell must be True on linux
        project_path = self.GetPrev().GetProjectLocation()
        if not os.path.exists(project_path):
            os.makedirs(project_path)
        p = subprocess.Popen(command,shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,cwd=project_path)
        stdout_thread = outputthread.SynchronizeOutputThread(p.stdout,p,progress_dlg)
        stdout_thread.start()
        stderr_thread = outputthread.SynchronizeOutputThread(p.stderr,p,progress_dlg)
        stderr_thread.start()
        p.wait()
        return p.returncode

    def CloneProject(self,progress_dlg):
        progress_dlg.call_back = progress_dlg.AppendMsg
        command = "git clone --progress %s"%self.addr_var.get().strip()
        ret_code = self.ExecCommandAndOutput(command,progress_dlg)
        msg = progress_dlg.label_var.get()
        progress_dlg.destroy()
        if ret_code != 0:
            messagebox.showerror(_("Clone project error"),_("%s")%msg,parent=self)
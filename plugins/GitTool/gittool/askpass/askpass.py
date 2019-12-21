import tkinter as tk
from tkinter import ttk,messagebox
import os
import sys
import subprocess
import platform
DEFAUT_CONTRL_PAD_X = 10
DEFAUT_CONTRL_PAD_Y = 10

password_txt = os.path.join(os.path.expanduser("~"),"pass.txt")

def remove_password():
    try:
        os.remove(password_txt)
    except:
        pass
def main():
    def ok():
        if store_secure_var.get():
            if platform.system() == "Windows":
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = subprocess.SW_HIDE
            else:
                startupinfo = None
            subprocess.Popen("git config --global credential.helper store",shell=True,startupinfo=startupinfo)
        print (name_var.get().strip(),)
        with open(password_txt,"w") as f:
            f.write(password_var.get())
        root.destroy()
        
    def cancel():
        print ("+++++")
        with open(password_txt,"w") as f:
            f.write("===========")
        root.destroy()
        
    root = tk.Tk()
    root.title("Login")
    w,h=310,180
    # Disable resizing the GUI
    root.resizable(0,0)
    root.geometry("{}x{}".format(w, h))
    ttk.Label(root,text='Username:').grid(column=0, row=1, sticky="nsew",padx=10,pady=(10,0))
    name_var = tk.StringVar()
    name_entry = ttk.Entry(root,textvariable=name_var)
    name_entry.grid(column=1, row=1, sticky="nsew",pady=(10,0),padx=(0,10))
    
    ttk.Label(root,text='Password:').grid(column=0, row=2, sticky="nsew",padx=10,pady=(10,0))
    password_var = tk.StringVar()
    password_entry = ttk.Entry(root,textvariable=password_var,show='*')
    password_entry.grid(column=1, row=2, sticky="nsew",pady=(10,0),padx=(0,10))
    
    store_secure_var = tk.BooleanVar(value=False)
    store_secure_btn = ttk.Checkbutton(root,text='Store in Secure Store',variable=store_secure_var)
    store_secure_btn.grid(column=0, row=3, sticky="nsew",columnspan=2,padx=10,pady=10)
    
    bottom_frame = ttk.Frame(root)
    space_label = ttk.Label(bottom_frame,text="")
    space_label.grid(column=0, row=0, sticky=tk.EW, padx=(DEFAUT_CONTRL_PAD_X, DEFAUT_CONTRL_PAD_X), pady=DEFAUT_CONTRL_PAD_Y)
    ok_button = ttk.Button(bottom_frame, text="Login",command=ok,default=tk.ACTIVE,takefocus=1)
    ok_button.grid(column=1, row=0, sticky=tk.EW, padx=(0, DEFAUT_CONTRL_PAD_X), pady=(0,DEFAUT_CONTRL_PAD_Y))
    cancel_button = ttk.Button(bottom_frame, text="Cancel", command=cancel)
    root.protocol("WM_DELETE_WINDOW", cancel)
    cancel_button.grid(column=2, row=0, sticky=tk.EW, pady=(0,DEFAUT_CONTRL_PAD_Y))
    bottom_frame.columnconfigure(0, weight=1)
    ok_button.focus_set()
    bottom_frame.grid(column=0, row=4, sticky="nsew",columnspan=2,padx=10,pady=10)
    #设置回车键关闭对话框
    ok_button.bind("<Return>", ok, True)
    root.mainloop()

if __name__ == "__main__":
    is_username = sys.argv[1].find("Username ") != -1
    if is_username:
        remove_password()
    if is_username:
        main()
    else:
        with open(password_txt) as f:
            print (f.read().strip(),)
        remove_password()
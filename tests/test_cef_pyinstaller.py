import cefpython3
import subprocess
import os

# 获取cefpython3包提供的hello_world.py文件
hd_file = os.path.dirname(cefpython3.__file__) + "\\examples\\hello_world.py"
print("*******打包cefpython3应用：", hd_file)

# 相当于执行打包命令： Pyinstaller hello_world.py
subprocess.run("Pyinstaller --hidden-import json {}".format(hd_file))
print("********打包成功!*******")

# 打包完成后，尝试启动可执行程序hello_world.exe
print("********开始执行，成功打包的应用：")
subprocess.run("./dist/hello_world/hello_world.exe")
# 如果执行后能出现标题为hell_world的弹窗，那恭喜你，否则继续往下看！
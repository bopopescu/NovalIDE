# -*- coding: utf-8 -*-

from distutils.core import setup
from setuptools import find_packages


import os
def list_files(directory):
    files = []
    for filename in os.listdir(directory):
        file_path = os.path.join(directory,filename)
        files.append(file_path)
    return files

setup(name='CodeCounter',
        version='1.0.2',
        description='''统计代码行数的插件。可统计此IDE支持的所有代码文件的空行数、注释行数和有效代码行数。对纯文本文件则会统计总行数及空行数。''',
        author='侯展意',
        author_email='1295752786@qq.com',
        url='',
        license='Mulan',
        packages=find_packages(),
        install_requires=[],
        zip_safe=False,
        package_data={'':['*.png','*.po']},#,'locale':['locale/*','locale/zh_CN/*','locale/en_US/*']},
        data_files = [('codecounter/locale/en_US/LC_MESSAGES',list_files('codecounter/locale/en_US/LC_MESSAGES')),\
                ('codecounter/locale/zh_CN/LC_MESSAGES',list_files('codecounter/locale/zh_CN/LC_MESSAGES'))],
        classifiers=[
            
        ],
        keywords = '',
        entry_points="""
        [Noval.plugins]
        CodeCounter = codecounter:CodeCounterPlugin
        """
)

from shutil import copyfile
copyfile('/media/hzy/程序/novalide/forgitcommit/NovalIDE/plugins/CodeCounter/dist/CodeCounter-1.0.2-py3.6.egg',
         '/home/hzy/.Noval/plugins/CodeCounter-1.0.2-py3.6.egg')

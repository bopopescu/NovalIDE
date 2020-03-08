# -*- coding: utf-8 -*-
from distutils.core import setup
from setuptools import find_packages


setup(name='AutoCompletion',
        version='1.0',
        description='''这是一个自动完成增强功能的插件,支持边输入或退格边提示,可以很好地辅助写代码''',
        author='',
        author_email='',
        url='',
        license='Mulan',
        packages=find_packages(),
        install_requires=[],
        zip_safe=False,
        package_data={},
        data_files = [],
        classifiers=[
            
        ],
        keywords = '',
        entry_points="""
        [Noval.plugins]
        AutoCompletion = autocompletion:AutoCompletionPlugin
        """
)


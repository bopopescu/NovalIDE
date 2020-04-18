# -*- coding: utf-8 -*-
from distutils.core import setup
from setuptools import find_packages
import platform

data_files = {
    'openwebbrowser':['resources/*.png','feeds.json']
}

setup(name='OpenWebBrowser',
        version='1.0',
        description='''这是内部web浏览器''',
        author='wukan',
        author_email='wekay102200@sohu.com',
        url='',
        license='Mulan',
        packages=find_packages(),
        install_requires=[],
        zip_safe=False,
        package_data=data_files,
        data_files = [],
        classifiers=[
            
        ],
        keywords = '',
        entry_points="""
        [Noval.plugins]
        OpenWebBrowser = openwebbrowser:WebBrowserPlugin
        """
)


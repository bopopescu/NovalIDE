# -*- coding: utf-8 -*-
from distutils.core import setup
from setuptools import find_packages


setup(name='DjangoKit',
        version='1.0',
        description='''Django是一个开放源代码的Web应用框架，由Python写成。采用了MTV的框架模式，即模型M，视图V和模版T。
                        它最初是被开发来用于管理劳伦斯出版集团旗下的一些以新闻内容为主的网站的，即是CMS（内容管理系统）软件。并于2005年7月在BSD许可证下发布。
                        这套框架是以比利时的吉普赛爵士吉他手Django Reinhardt来命名的，这个插件可以一键式生成Django框架代码。''',
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
        Django = djangokit:DjangoPlugin
        """
)


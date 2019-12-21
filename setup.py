from distutils.core import setup
from setuptools import find_packages
import os
import sys

def list_files(directory):
    files = []
    for filename in os.listdir(directory):
        file_path = os.path.join(directory,filename)
        files.append(file_path)
    return files

if sys.version_info < (3, 5):
    raise RuntimeError("NovalIDE requires Python 3.5 or later")

with open("version.txt") as f:
    version = f.read()

with open('requirements.txt') as f:
    install_requires = [line for line in f.read().split() if not line.startswith('#')]

data_list = [
    'data/intellisence/builtins/2/*',
    'data/intellisence/builtins/3/*',
    'data/template/*.tar.bz2',
    'data/sample/*.sample',
    'data/styles/*.ess',
    'data/*.txt',
    'syntax/lexer/*.py',
    'python/syntax/lexer/*.py',
    'bmp_source/project/python/*', 
    'bmp_source/project/*', 
    'bmp_source/python/debugger/*',
    'bmp_source/python/outline/*',
    'bmp_source/python/*',
    'bmp_source/template/*',
    'bmp_source/file/*', 
    'bmp_source/files/*', 
    'bmp_source/checkbox/*', 
    'bmp_source/toolbar/*', 
    'bmp_source/*.*'
]
setup(name='NovalIDE',
        version = version,
        description='''NovalIDE is a cross platform Python IDE''',
        author='wukan',
        author_email='wekay102200@sohu.com',
        url='https://github.com/noval102200/NovalIDE.git',
        license='Genetalks',
        packages=find_packages(),
        install_requires=install_requires,
        zip_safe=False,
        test_suite='noval.tests',
        package_data={
            'noval':data_list
        },
        data_files = [('',['version.txt','template.xml','noval.ico']),('locale/en_US/LC_MESSAGES',list_files('locale/en_US/LC_MESSAGES')),\
                ('locale/zh_CN/LC_MESSAGES',list_files('locale/zh_CN/LC_MESSAGES')),('tkdnd',list_files('tkdnd'))],
        classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy'
        ],
        entry_points="""
        [gui_scripts]
        NovalIDE = noval.python.run:main
        """
)



from distutils.core import setup
from setuptools import find_packages

with open("version.txt") as f:
    version = f.read()

install_requires = ["watchdog","chardet","pyperclip","psutil","requests","pycryptodome",'mss','pillow']
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
            'noval': [
                    'tool/data/intellisence/builtins/2/*',
                    'tool/data/intellisence/builtins/3/*',
                    'tool/data/template/*.tar.bz2',
                    'tool/data/sample/*.sample',
                    'tool/data/styles/*.ess',
                    'tool/data/*.txt',
                    'tool/bmp_source/template/*', 
                    'tool/syntax/lexer/*.py',
                    'tool/bmp_source/toolbar/*', 
                    'tool/bmp_source/project/*', 
                    'tool/bmp_source/debugger/*', 
                    'tool/bmp_source/web/*', 
                    'tool/bmp_source/*.*', 
                    'locale/en_US/LC_MESSAGES/*.mo',
                    'locale/zh_CN/LC_MESSAGES/*.mo'
                    ],
        },
        data_files = [('',['version.txt','template.xml']),],
        classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy'
        ],
        entry_points="""
        [console_scripts]
        NovalIDE = noval.noval:main
        """
)



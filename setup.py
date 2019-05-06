import sys
if sys.platform == "win32":
    from distutils.core import setup
    import py2exe
    import glob
    import modulefinder
    import win32com.client
    is_debug = False
    
    #this block code used to add win32com.shell and win32com.shellcon module to library.zip
    ###******************************************###########
    for p in win32com.__path__[1:]:
        modulefinder.AddPackagePath('win32com', p)
    for extra in ['win32com.taskscheduler']:
        __import__(extra)
        m = sys.modules[extra]
        for p in m.__path__[1:]:
            modulefinder.AddPackagePath(extra, p)
    ###******************************************###########
    
    for i,argv in enumerate(sys.argv):
        if argv == "debug" or argv == "-debug":
            is_debug = True
            del sys.argv[i]
            
    data_files = [
        ("noval/bmp_source", glob.glob("noval/bmp_source/*.ico") + glob.glob("noval/bmp_source/*.jpg") \
                             + glob.glob("noval/bmp_source/*.png") + glob.glob("noval/bmp_source/*.gif")),
        ("noval/bmp_source/toolbar",glob.glob("noval/bmp_source/toolbar/*.png")),
        ("noval/bmp_source/file",glob.glob("noval/bmp_source/file/*.png")+glob.glob("noval/bmp_source/file/*.gif")),
        ("noval/bmp_source/files",glob.glob("noval/bmp_source/files/*.png")+glob.glob("noval/bmp_source/files/*.gif")),
        ("noval/bmp_source/project",glob.glob("noval/bmp_source/project/*.*")),
        ("noval/bmp_source/project/python",glob.glob("noval/bmp_source/project/python/*.*")),
        ("noval/bmp_source/python",glob.glob("noval/bmp_source/python/*.*")),
        ("noval/bmp_source/python/debugger",glob.glob("noval/bmp_source/python/debugger/*.png") \
                                                        + glob.glob("noval/bmp_source/debugger/*.ico")),
                                                        
        ("noval/bmp_source/python/outline",glob.glob("noval/bmp_source/python/outline/*.*")),
        ("noval/bmp_source/template",glob.glob("noval/bmp_source/template/*.*")),
        ("noval/debugger",glob.glob("noval/debugger/DebuggerHarness.py")),
        ("noval/debugger",glob.glob("noval/debugger/DebuggerHarness3.py")),
        ("noval/data",["noval/data/tips.txt"]),
        ("noval/data",["noval/data/tips_zh_CN.txt"]),
        ("noval/data/template",glob.glob("noval/data/template/*.tar.bz2")),
        ("noval/data/sample",glob.glob("noval/data/sample/*.sample")),
        ("noval/data/styles",glob.glob("noval/data/styles/*.ess")),
        ("noval/syntax/lexer",glob.glob("noval/syntax/lexer/*.py")),
        ("noval/python/syntax/lexer",glob.glob("noval/python/syntax/lexer/*.py")),
          ("locale/en_US/LC_MESSAGES",['locale/en_US/LC_MESSAGES/novalide.mo']),
           ("locale/zh_CN/LC_MESSAGES",['locale/zh_CN/LC_MESSAGES/novalide.mo',\
                        'locale/zh_CN/LC_MESSAGES/wxstd.mo',\
                        'locale/zh_CN/LC_MESSAGES/wxstock.mo',]),
           ('',['version.txt','template.xml'])
    ]
    options = { "py2exe":{"dll_excludes":["MSVCP90.dll"],"packages": ['PIL.IcoImagePlugin','csv','noval.syntax.syndata']}}

    if is_debug:
        print 'executable run in console mode'
        setup(console=[{"script":"NovalIDE.py","icon_resources":[(1, u"noval.ico")]}],
              options = options,
                data_files=data_files,)
    else:
        print 'executable run in windows mode'
        setup(windows=[{"script":"NovalIDE.py","icon_resources":[(1, u"noval.ico")]}],
              options = options,
                data_files=data_files,)

elif sys.platform.find('linux') != -1:
    from distutils.core import setup
    from setuptools import find_packages
    
    with open("version.txt") as f:
        version = f.read()

    install_requires = ["watchdog","chardet","pyperclip","psutil","requests","pycryptodome"]
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



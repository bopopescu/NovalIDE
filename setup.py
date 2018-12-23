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

    if is_debug:
        print 'executable run in console mode'
        setup(console=[{"script":"NovalIDE.py","icon_resources":[(1, u"noval.ico")]}],
              options = { "py2exe":{"dll_excludes":["MSVCP90.dll"],"packages": ['wx.lib.pubsub','csv','noval.tool.syntax.syndata']}},
                data_files=[("noval/tool/bmp_source", glob.glob("noval/tool/bmp_source/*.ico") + glob.glob("noval/tool/bmp_source/*.jpg") \
                             + glob.glob("noval/tool/bmp_source/*.png") + glob.glob("noval/tool/bmp_source/*.gif")),
                    ("noval/tool/bmp_source/toolbar",glob.glob("noval/tool/bmp_source/toolbar/*.png")),
                    ("noval/tool/bmp_source/web",glob.glob("noval/tool/bmp_source/web/*.png")),
                    ("noval/tool/bmp_source/project",glob.glob("noval/tool/bmp_source/project/*.png")+glob.glob("noval/tool/bmp_source/project/*.gif")+glob.glob("noval/tool/bmp_source/project/*.ico")),
                    ("noval/tool/bmp_source/debugger",glob.glob("noval/tool/bmp_source/debugger/*.png") \
                                                        + glob.glob("noval/tool/bmp_source/debugger/*.ico")),
                    ("noval/tool/bmp_source/template",glob.glob("noval/tool/bmp_source/template/*.*")),
                    ("noval/tool/data",["noval/tool/data/tips.txt"]),
                     ("noval/parser",glob.glob("noval/parser/*.py")),
                     ("noval/tool/syntax/lexer",glob.glob("noval/tool/syntax/lexer/*.py")),
                      ("noval/locale/en_US/LC_MESSAGES",['noval/locale/en_US/LC_MESSAGES/novalide.mo']),
                       ("noval/locale/zh_CN/LC_MESSAGES",['noval/locale/zh_CN/LC_MESSAGES/novalide.mo']),],)
    else:
        print 'executable run in windows mode'
        setup(windows=[{"script":"NovalIDE.py","icon_resources":[(1, u"noval.ico")]}],
              options = { "py2exe":{"dll_excludes":["MSVCP90.dll"],"packages": ['wx.lib.pubsub','csv','noval.tool.syntax.syndata']}},
                data_files=[("noval/tool/bmp_source", glob.glob("noval/tool/bmp_source/*.ico") + glob.glob("noval/tool/bmp_source/*.jpg") \
                             + glob.glob("noval/tool/bmp_source/*.png") + glob.glob("noval/tool/bmp_source/*.gif")),
                    ("noval/tool/bmp_source/toolbar",glob.glob("noval/tool/bmp_source/toolbar/*.png")),
                    ("noval/tool/bmp_source/web",glob.glob("noval/tool/bmp_source/web/*.png")),
                    ("noval/tool/bmp_source/project",glob.glob("noval/tool/bmp_source/project/*.png")+glob.glob("noval/tool/bmp_source/project/*.gif")+glob.glob("noval/tool/bmp_source/project/*.ico")),
                    ("noval/tool/bmp_source/debugger",glob.glob("noval/tool/bmp_source/debugger/*.png") \
                                                        + glob.glob("noval/tool/bmp_source/debugger/*.ico")),
                    ("noval/tool/bmp_source/template",glob.glob("noval/tool/bmp_source/template/*.*")),
                    ("noval/tool/debugger",glob.glob("noval/tool/debugger/DebuggerHarness.py")),
                    ("noval/tool/debugger",glob.glob("noval/tool/debugger/DebuggerHarness3.py")),
                    ("noval/tool/data",["noval/tool/data/tips.txt"]),
                    ("noval/tool/data",["noval/tool/data/tips_zh_CN.txt"]),
                    ("noval/tool/data/template",glob.glob("noval/tool/data/template/*.tar.bz2")),
                    ("noval/tool/data/sample",glob.glob("noval/tool/data/sample/*.sample")),
                    ("noval/tool/data/styles",glob.glob("noval/tool/data/styles/*.ess")),
                    ("noval/tool/syntax/lexer",glob.glob("noval/tool/syntax/lexer/*.py")),
                     ("noval/parser",glob.glob("noval/parser/*.py")),
                      ("noval/locale/en_US/LC_MESSAGES",['noval/locale/en_US/LC_MESSAGES/novalide.mo']),
                       ("noval/locale/zh_CN/LC_MESSAGES",['noval/locale/zh_CN/LC_MESSAGES/novalide.mo',\
                                    'noval/locale/zh_CN/LC_MESSAGES/wxstd.mo',\
                                    'noval/locale/zh_CN/LC_MESSAGES/wxstock.mo',]),
                       ('',['version.txt','template.xml'])],)

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



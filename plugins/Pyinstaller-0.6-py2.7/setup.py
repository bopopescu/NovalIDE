from distutils.core import setup
from setuptools import find_packages

setup(name='Pyinstaller',
        version='1.0',
        description='''use pyinstaller tool to convert to python project to windows exe''',
        author='wukan',
        author_email='wekay102200@sohu.com',
        url='http://www.novalide.com',
        license='wxWindows',
        packages=find_packages(),
        install_requires=[],
        zip_safe=False,
        package_data={'pyinstaller': ['locale/zh_CN/LC_MESSAGES/pyinstaller.mo']},
        classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy'
        ],
        entry_points="""
        [Noval.plugins]
        Pyinstaller = pyinstaller:Pyinstaller
        """
)

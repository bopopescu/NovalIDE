from distutils.core import setup
from setuptools import find_packages

setup(name='Pyinstaller',
        version='1.2',
        description='''PyInstaller bundles a Python application and all its dependencies into a single package.The user can run the packaged app without installing a Python interpreter or any modules''',
        author='wukan',
        author_email='wekay102200@sohu.com',
        url='http://www.novalide.com',
        license='wxWindows',
        packages=find_packages(),
        install_requires=[],
        zip_safe=False,
        package_data={'pyinstaller': ['locale/zh_CN/LC_MESSAGES/pyinstaller.mo','file_version_info.txt']},
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

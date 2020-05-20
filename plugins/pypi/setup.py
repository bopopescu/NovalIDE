from distutils.core import setup
from setuptools import find_packages

setup(name='PyPI',
        version='1.4',
        description='''a simple tool to enable user publish package to local site-packages or pypi server conveniently via new pypi project''',
        author='wukan',
        author_email='wekay102200@sohu.com',
        url='http://www.novalide.com',
        license='wxWindows',
        packages=find_packages(),
        install_requires=[],
        zip_safe=False,
        package_data={'pypi': ['package_template.tar.bz2','package_tool_template.tar.bz2','locale/zh_CN/LC_MESSAGES/pypi.mo']},
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
        [Noval.plugins]
        PyPI = pypi:PyPi
        """
)

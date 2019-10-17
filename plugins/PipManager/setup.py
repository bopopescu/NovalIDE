from distutils.core import setup
from setuptools import find_packages


setup(name='PipManager',
        version='1.0',
        description='''this plugin is used to search,get,download install,uninstall and update pip package from pypi''',
        author='wukan',
        author_email='kan.wu@gentalks.com',
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
        PipManager = pipmanager:PipManagerPlugin
        """
)


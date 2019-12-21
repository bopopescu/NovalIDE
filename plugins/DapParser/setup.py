from distutils.core import setup
from setuptools import find_packages


setup(name='DapParser',
        version='1.1',
        description='''cloudwms dap file parser''',
        author='wukan',
        author_email='kan.wu@genetalks.com',
        url='http://www.genetalks.com',
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
        DapParser = dapparser:DapParserPlugin
        """
)


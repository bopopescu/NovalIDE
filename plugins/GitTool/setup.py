from distutils.core import setup
from setuptools import find_packages


setup(name='GitTool',
        version='1.0',
        description='''a plugin support push commit add and pull git files from remote git server''',
        author='wukan',
        author_email='kan.wu@genetalks.com',
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
        GitTool = gittool:GitToolPlugin
        """
)


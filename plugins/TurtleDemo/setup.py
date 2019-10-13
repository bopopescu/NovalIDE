from distutils.core import setup
from setuptools import find_packages


setup(name='PyTurtleDemo',
        version='1.0',
        description='''this is a demo of tutle in python3.5 or later''',
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
        PyTurtleDemo = pyturtledemo:TurtleDemoPlugin
        """
)


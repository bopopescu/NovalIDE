from distutils.core import setup
from setuptools import find_packages


setup(name='PyTurtleDemo',
        version='1.1',
        description='''this is a demo of Turtle graphics in python3.5 or later,you can view in &Hep menu after install it''',
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


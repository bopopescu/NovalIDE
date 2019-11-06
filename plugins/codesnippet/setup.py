from distutils.core import setup
from setuptools import find_packages


setup(name='CodeSnippet',
        version='1.0',
        description='''a lot of code demo of python classified by program purpose''',
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
        CodeSnippet = codesnippet:CodeSnippetPlugin
        """
)


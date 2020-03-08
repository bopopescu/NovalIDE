from distutils.core import setup
from setuptools import find_packages


setup(name='TomorrowSyntaxTheme',
        version='1.0',
        description='''serial syntax theme of tomorrow style''',
        author='wukan',
        author_email='wekay102200@sohu.com',
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
        TomorrowSyntaxTheme = tomorrowsyntaxtheme:TomorrowSyntaxThemePlugin
        """
)


from distutils.core import setup
from setuptools import find_packages
import platform
data_files = {}
if platform.system() == "Windows":
   data_files = {
        'gittool':['./askpass/dist/askpass.exe']
    }
else:
    data_files = {
        'gittool':['./askpass/askpass.py']
    }
    
data_files['gittool'].append('res/*.*')
setup(name='GitTool',
        version='1.0',
        description='''GitTool is a graphical Git client plugin with support for Git and Pull Requests for GitHub, Gitee and so on. it runs on Windows and Linux os system''',
        author='wukan',
        author_email='kan.wu@genetalks.com',
        url='',
        license='Mulan',
        packages=find_packages(),
        install_requires=[],
        zip_safe=False,
        package_data=data_files,
        data_files = [],
        classifiers=[
        ],
        keywords = '',
        entry_points="""
        [Noval.plugins]
        GitTool = gittool:GitToolPlugin
        """
)


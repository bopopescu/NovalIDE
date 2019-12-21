from distutils.core import setup
from setuptools import find_packages


setup(name='ShellEditor',
        version='1.0',
        description='''ShellEditor is a shell script development plugin for the NovalIDE, providing a rich edition experience through integration with the Bash Language Server.''',
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
        ShellEditor = shelleditor:ShellEditorPlugin
        """
)


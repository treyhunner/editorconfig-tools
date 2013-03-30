from setuptools import setup
import editorconfig_tools

required = ['editorconfig', 'clint']

setup(
    name='EditorConfig Tools',
    #version=editorconfig_tools.__version__,
    author='EditorConfig Team',
    packages=['editorconfig_tools'],
    install_requires=required,
    license='LICENSE',
    description='Tools for correcting files based on EditorConfig files',
    long_description=open('README.rst').read(),
    entry_points={
        'console_scripts': [
            'fix_editorconfig = fix_editorconfig:main',
            'check_editorconfig = check_editorconfig:main',
        ]
    },
)

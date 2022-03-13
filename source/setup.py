import shutil
import os.path as op

from setuptools import setup
from setuptools.command.install import install


setup(
	name='todocli',
	version='3.4.2',
	packages=['todo', 'todo.bash_completion'],
	entry_points={
		'console_scripts': [
			'todo = todo.todo:main'
		]
	},
	include_package_data=True,
    install_requires=[
        'setuptools==60.9.3',
    ],
    extras_require={
        'tests': {
            'pyfakefs==4.5.5',
        },
    },
	author='foobuzz',
	author_email='foobuzz@fastmail.com',
	description='A command line todo list manager',
	keywords='command line todo list',
	url='https://github.com/foobuzz/todo',
	license='MIT'
)

import shutil
import os.path as op

from setuptools import setup
from setuptools.command.install import install


setup(
	name='todocli',
	version='5.0.0',
	python_requires='>=3.8',
	packages=['todo', 'todo.bash_completion'],
	entry_points={
		'console_scripts': [
			'todo = todo.todo:main'
		]
	},
	include_package_data=True,
    install_requires=[
        'setuptools==65.5.1',
    ],
    extras_require={
        'tests': {
            'freezegun==1.2.2',
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

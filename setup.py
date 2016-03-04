from setuptools import setup

setup(
	name='todocli',
	version='1.0.2',
	py_modules=['todo'],
	entry_points={
		'console_scripts': [
			'todo = todo:main'
		]
	},
	test_suite='tests',

	author='foobuzz',
	author_email='dprosium@gmail.com',
	description='A command line todo list manager',
	keywords='command line todo list',
	url='https://github.com/foobuzz/todo'
)
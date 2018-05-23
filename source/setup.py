import shutil
import os.path as op

from setuptools import setup
from setuptools.command.install import install
from pkg_resources import Requirement, resource_filename


BASH_COMPLETION = '/etc/bash_completion.d'
SOURCE_COMPLETION = 'bash_completion/toduh.sh'


class PostInstallCommand(install):

	def run(self):
		install.run(self)
		if op.exists(BASH_COMPLETION) and op.isdir(BASH_COMPLETION):
			requirement = Requirement.parse("todocli")
			filename = resource_filename(requirement, SOURCE_COMPLETION)
			try:
				shutil.copy(filename, BASH_COMPLETION)
			except:
				print('Installation of auto-completion script failed. '
					'Please use sudo.')


setup(
	name='todocli',
	version='3.1.2',
	packages=['todo'],
	entry_points={
		'console_scripts': [
			'todo = todo.todo:main'
		]
	},
	include_package_data = True,
	data_files=[
		('bash_completion/toduh.sh', ['bash_completion/toduh.sh'])
	],
	cmdclass={
		'install': PostInstallCommand
	},
	install_requires=['docopt==0.6.2'],
	author='foobuzz',
	author_email='dprosium@gmail.com',
	description='A command line todo list manager',
	keywords='command line todo list',
	url='https://github.com/foobuzz/todo',
	license='MIT'
)

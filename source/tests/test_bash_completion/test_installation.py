import unittest.mock
import os
import os.path as op
import sys
from pathlib import Path

import pkg_resources
from pyfakefs.fake_filesystem_unittest import TestCase

sys.path.insert(1, op.abspath('./todo'))

from todo.bash_completion import installation
from todo.bash_completion.installation import TODO_AUTOCOMPLETION_MARK


class BaseTestInstallAutocompletion(TestCase):
	def setUp(self):
		# Global definition of Path instances requires us to make pyfakefs reload
		# the module
		self.setUpPyfakefs(modules_to_reload=[installation])
		
		# We arbitrarily use .zshrc for those tests
		self.config_filepath = str(Path.home() / '.zshrc')
		self.fs.create_file(self.config_filepath)

		# We also need to have the toduh.sh source script exists where
		# pkg_resources thinks it does.
		filename = pkg_resources.resource_filename(
			'todo.bash_completion', 'toduh.sh'
		)
		os.makedirs(str(Path(filename).parent), exist_ok=True)
		with open(filename, 'w') as f:
			# We're using fake contents for the script. The goal is to check
			# that it has been properly copied.
			f.write("[trust me this is the script]")


class TestInstallAutocompletionNotAlreadyInstalled(BaseTestInstallAutocompletion):

	def test(self):
		with unittest.mock.patch('builtins.print') as mocked_print:
			installation.install_autocompletion()

		with open(self.config_filepath) as f:
			contents = f.read()

		self.assertIn(TODO_AUTOCOMPLETION_MARK, contents)
		self.assertIn("[trust me this is the script]", contents)
		self.assertIn(
			"Autocompletion installed",
			mocked_print.mock_calls[0][1][0]
		)


class TestInstallAutocompletionAlreadyInstalled(BaseTestInstallAutocompletion):

	def setUp(self):
		super().setUp()

		with open(self.config_filepath, 'w') as f:
			f.write(TODO_AUTOCOMPLETION_MARK)


	def test(self):
		with unittest.mock.patch('builtins.print') as mocked_print:
			installation.install_autocompletion()

		with open(self.config_filepath) as f:
			contents = f.read()

		self.assertEqual(contents.count(TODO_AUTOCOMPLETION_MARK), 1)
		self.assertIn(
			"Autocompletion is already installed",
			mocked_print.mock_calls[0][1][0]
		)


class TestInstallAutocompletionNoConfigFile(BaseTestInstallAutocompletion):

	def setUp(self):
		super().setUp()
		
		os.remove(self.config_filepath)


	def test(self):
		with unittest.mock.patch('builtins.print') as mocked_print:
			installation.install_autocompletion()

		self.assertFalse(Path(self.config_filepath).exists())
		self.assertIn(
			"No appropriate config file was found",
			mocked_print.mock_calls[0][1][0]
		)

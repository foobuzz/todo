#! /usr/bin/env python3

import unittest, sys, os, functools, argparse
import os.path as op

sys.path.insert(0, op.abspath('.'))
sys.path.insert(1, op.abspath('./todo'))

import tests.utils as utils
import test_todo, test_utils # pylint: disable=W0611

import todo.todo as todo
import todo.utils as tutils
from todo.config import DATA_LOCATION, CONFIG_FILE


NOW = todo.NOW

TEST_CONFIG = 'tests/.toduhrc'
TEST_DATA_FILE = 'tests/.todo_datafile'

UNIT_TESTS = [
	'test_todo',
	'test_utils'
]


def test_trace(print_commands=False):
	# Backuping the datafile and removing the original
	data_backup = utils.backup_and_replace(DATA_LOCATION, TEST_DATA_FILE)
	# Backuping the config file and replace it with ours (colors disabled)
	config_backup = utils.backup_and_replace(CONFIG_FILE, TEST_CONFIG)
	try:
		get_dt = functools.partial(tutils.get_datetime, now=NOW)
		errors = utils.test_trace('tests/cmd_trace', get_dt, print_commands)
		if errors['clash'] == 0 and errors['crash'] == 0:
			print('OK')
		else:
			print('FAIL')
	finally:
		if data_backup is not None:
			os.rename(data_backup, DATA_LOCATION)
		if config_backup is not None:
			os.rename(config_backup, CONFIG_FILE)


if __name__ == '__main__':
	parser = argparse.ArgumentParser(description='todo test suite')
	parser.add_argument('-a', '--all', action='store_true',
		help="Run functional test in addition to unit tests")
	parser.add_argument('-f', '--func', action='store_true',
		help="Run only functional test")
	parser.add_argument('-v', '--verbose', action='store_true',
		help="Prints the commands being ran during functional test")
	args = parser.parse_args()

	if not args.func:
		suite = unittest.TestSuite()
		test_loader = unittest.TestLoader()
		for module in UNIT_TESTS:
			mod_suite = test_loader.loadTestsFromModule(sys.modules[module])
			suite.addTests(mod_suite)
		print('* Unit tests'.format(module))
		unittest.TextTestRunner().run(suite)
	if args.func or args.all:
		print('* Fonctional tests')
		test_trace(args.verbose)

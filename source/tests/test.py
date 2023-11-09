#! /usr/bin/env python3

import unittest, sys, os, functools, argparse
import os.path as op

from . import utils
from . import (
	test_todo,
	test_utils,
	test_rainbow,
	test_text_wrap,
)
from .test_bash_completion import test_installation

sys.path.insert(0, op.abspath('.'))

import todo.todo as todo
import todo.cli_parser as cli_parser
from todo.data_access import DB_PATH as DATA_LOCATION
from todo.todo import CONFIG_FILE
from todo.utils import VERSION_PATH


NOW = todo.NOW

TEST_CONFIG = 'tests/.toduhrc'

UNIT_TESTS = [
	'tests.test_todo',
	'tests.test_utils',
	'tests.test_rainbow',
	'tests.test_text_wrap',
	'tests.test_bash_completion.test_installation',
]

TRACES_DIR = 'tests/traces'

TEST_REPLACEMENTS = [
	(DATA_LOCATION, None),
	(VERSION_PATH, None),
	(CONFIG_FILE, TEST_CONFIG)
]


class TestSetup:

	def __init__(self, replacements=TEST_REPLACEMENTS):
		self.replacements = {repl: None for repl in replacements}

	def __enter__(self):
		for source, repl in self.replacements:
			backup = utils.backup_and_replace(source, repl)
			self.replacements[(source, repl)] = backup
		return self

	def __exit__(self, *args):
		for (source, repl), backup in self.replacements.items():
			os.rename(backup, source)


def test_trace(trace_file, print_commands=False):
	with TestSetup() as setup:
		get_dt = functools.partial(cli_parser._parse_datetime, now=NOW)
		errors = utils.test_trace(trace_file, get_dt, print_commands)
		if errors['clash'] == 0 and errors['crash'] == 0:
			print('OK')
		else:
			print('FAIL')


def main():
	parser = argparse.ArgumentParser(description='todo test suite')
	parser.add_argument('-a', '--all', action='store_true',
		help="Run functional test in addition to unit tests")
	parser.add_argument('-f', '--func', action='store_true',
		help="Run only functional test")
	parser.add_argument('-v', '--verbose', action='store_true',
		help="Prints the commands being ran during functional test")
	parser.add_argument('-b', '--build', action='store',
		dest='build',
		help="Build a trace file")
	parser.add_argument('-o', '--out', action='store',
		dest='out',
		help="Destination of a trace build")
	args = parser.parse_args()

	if args.build is not None:
		out = args.build
		if args.out is not None:
			out = args.out
		with TestSetup() as setup:
			utils.run_trace(args.build, out)
		sys.exit(0)

	if not args.func:
		suite = unittest.TestSuite()
		test_loader = unittest.TestLoader()
		for module in UNIT_TESTS:
			mod_suite = test_loader.loadTestsFromModule(sys.modules[module])
			suite.addTests(mod_suite)
		print('* Unit tests')
		unittest.TextTestRunner().run(suite)
	if args.func or args.all:
		print('* Fonctional tests')
		for filename in sorted(os.listdir(TRACES_DIR)):
			path = op.join(TRACES_DIR, filename)
			print('[{}]'.format(filename))
			test_trace(path, args.verbose)


if __name__ == '__main__':
	main()

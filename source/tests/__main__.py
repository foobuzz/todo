#! /usr/bin/env python3

import unittest, sys, os, functools, argparse
import os.path as op
from datetime import datetime, timedelta, timezone

sys.path.insert(0, op.abspath('.'))
sys.path.insert(1, op.abspath('./todo'))

import tests.utils as utils

import todo.todo as todo
from todo.todo import Task, Context
import todo.utils as tutils
from todo.config import DATA_LOCATION, CONFIG_FILE


NOW = todo.NOW

TEST_CONFIG = 'tests/.toduhrc'
TEST_DATA_FILE = 'tests/.todo_datafile'


class TestDatetimeParsing(unittest.TestCase):

	input_cases = {
		'2016-02-03': datetime(2016, 2, 3),
		'2016-02-03T19:30:04': datetime(2016, 2, 3, 19, 30, 4),
		'03/02/2016': None,
		'42s': NOW + timedelta(seconds=42),
		'42m': NOW + timedelta(seconds=42*60),
		'42h': NOW + timedelta(days=1, seconds=18*3600),
		'42d': NOW + timedelta(days=42),
		'42w': NOW + timedelta(days=42*7),
		'42n': None,
		'dkfnjdfkfd': None,
		'lol42n': None,
		'-42s': None,
		'1888888s': NOW + timedelta(seconds=1888888),
		'1.25s': None,
		'20l5-01-00': None
	}

	remaining_cases = {
		timedelta(seconds=15): '15 seconds',
		timedelta(seconds=65): '65 seconds',
		timedelta(seconds=126): '2 minutes',
		timedelta(seconds=60*44): '44 minutes',
		timedelta(seconds=60*44+18): '44 minutes',
		timedelta(seconds=3600): '60 minutes',
		timedelta(seconds=2*3600): '2 hours',
		timedelta(seconds=3600*4+60*10): '4 hours',
		timedelta(days=1): '24 hours',
		timedelta(days=1, seconds=8*3600): '32 hours',
		timedelta(days=1, seconds=8*3600+450): '32 hours',
		timedelta(days=2): '2 days',
		timedelta(days=2, seconds=3600*8): '2 days',
		timedelta(days=547545): '547545 days'
	}

	def test_parse_user_date(self):
		for u_input, expected in TestDatetimeParsing.input_cases.items():
			result = tutils.get_datetime(u_input, NOW)
			if expected is not None:
				# Converting expected manually-entered datetime into UTC
				expected = datetime.utcfromtimestamp(expected.timestamp())
				expected = expected.replace(tzinfo=timezone.utc)

				# The conversions to and back from timestamps introduce errors
				# in the range of 10-nanoseconds, but we only need a precision
				# of the second
				result = result.replace(microsecond=0)
				expected = expected.replace(microsecond=0)
				self.assertEqual(result, expected)
			else:
				self.assertEqual(result, None)

	def test_parse_remaining(self):
		for dt, expected in TestDatetimeParsing.remaining_cases.items():
			result = tutils.parse_remaining(dt)
			self.assertEqual(result, expected)


class TestContextAnalysis(unittest.TestCase):

	context_cases = {
		'': [],
		'hello': ['hello'],
		'hello.world': ['hello', 'world']
	}

	# (task's context, query context) : (hidden, discreet, wide)
	relevancy_cases = {
		('', ''): (True, True, True),
		('hello', 'hello'): (True, True, True),
		('hello.world', 'hello'): (False, True, True),
		('hello.world.yeah', 'hello.world'): (False, True, True),
		('hello.world.yeah', 'hello'): (False, True, True),
		('hello', ''): (False, True, True),
		('hello.world', ''): (False, False, True),
		('hello.world', 'hello.world'): (True, True, True),
		('hello', 'bonjour'): (False, False, False),
		('hello.bonjour', 'bonjour'): (False, False, False),
		('hello.bonjour', 'hey.bonjour'): (False, False, False)
	}

	def test_relevancy_test(self):
		root_ctx = Context('', None)
		task = Task(1, '', root_ctx)
		for i_vis, vis in enumerate(['hidden', 'discreet', 'wide']):
			task.visibility = vis
			for (t_ctx, q_ctx), expected in \
			TestContextAnalysis.relevancy_cases.items():
				task.context = root_ctx.add_contexts(t_ctx)
				root_ctx.add_contexts(q_ctx)
				result = task.is_relevant_to_context(root_ctx.get_context(q_ctx))
				self.assertEqual(result, expected[i_vis])


class TestTasksSort(unittest.TestCase):

	# A list of correctly sorted tasks. The test consists in sorting them
	# and checking that the sorted list is the same as the original
	ctx = Context('', None)
	tasks = [
		Task(0, '', ctx, created=NOW, priority=3),
		Task(1, '', ctx, created=NOW-timedelta(minutes=1), priority=2),
		Task(2, '', ctx, created=NOW-timedelta(minutes=2), deadline=NOW+timedelta(days=3)),
		Task(3, '', ctx, created=NOW-timedelta(minutes=3), deadline=NOW+timedelta(days=4)),
		Task(4, '', Context('world', None, priority=2), created=NOW-timedelta(minutes=6)),
		Task(5, '', ctx, created=NOW-timedelta(minutes=7)),
		Task(6, '', Context('hello', None), created=NOW-timedelta(minutes=5))
	]

	def test_task_sort(self):
		tasks_cpy = sorted(TestTasksSort.tasks,
			key=lambda t: t.order_infos())
		self.assertEqual(tasks_cpy, TestTasksSort.tasks)


class TestLimitStr(unittest.TestCase):

	cases = {
		('hello', 5): 'hello',
		('hello', 6): 'hello',
		('hello', 4): 'h...',
		('hello', 3): 'hel',
		('hello', 0): ''
	}

	def test_limit_str(self):
		for args, result in TestLimitStr.cases.items():
			self.assertEqual(tutils.limit_str(*args), result)


class TestDefaulting(unittest.TestCase):

	class Dummy(todo.HasDefaults):

		defaults = {
			'hello': 'world!',
			'answer': 42,
			'linux': 'interject'
		}

		def __init__(self):
			self.init_defaults()

	def test_defaulting(self):
		dummy1 = TestDefaulting.Dummy()
		dummy2 = TestDefaulting.Dummy()
		dummy2.answer = 43
		self.assertTrue(dummy1.is_default('hello'))
		self.assertTrue(dummy1.is_default('answer'))
		self.assertTrue(dummy1.is_default('linux'))
		self.assertTrue(dummy2.is_default('hello'))
		self.assertFalse(dummy2.is_default('answer'))
		self.assertTrue(dummy2.is_default('linux'))


def test_trace(print_commands=False):
	# Backuping the datafile and removing the original
	data_backup = utils.backup_and_replace(DATA_LOCATION, TEST_DATA_FILE)
	# Backuping the config file and replace it with ours (colors disabled)
	config_backup = utils.backup_and_replace(CONFIG_FILE, TEST_CONFIG)
	try:
		get_dt = functools.partial(tutils.get_datetime, now=NOW)
		utils.test_trace('tests/cmd_trace', get_dt, print_commands)
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
		test_loader = unittest.TestLoader()
		suite = test_loader.loadTestsFromModule(sys.modules[__name__])
		print('* Unit tests')
		unittest.TextTestRunner().run(suite)
	if args.func or args.all:
		print('* Fonctional tests')
		test_trace(args.verbose)
		print('OK')

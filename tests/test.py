#! /usr/bin/env python3

import unittest, sys, os, shutil
import os.path as op
from importlib import machinery
from datetime import datetime, timedelta, timezone

import utils

# import todo
# from todo import Task
todo_loader = machinery.SourceFileLoader('todo', 'todo.py')
todo = todo_loader.load_module()
Task = getattr(todo, 'Task')


NOW = todo.NOW


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
			result = todo.get_datetime(u_input)
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
			result = todo.parse_remaining(dt)
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

	def test_get_namespaces(self):
		for context, expected in TestContextAnalysis.context_cases.items():
			result = todo.get_namespaces(context)
			self.assertEqual(result, expected)

	def test_relevancy_test(self):
		task = Task(1, '')
		for i_vis, vis in enumerate(['hidden', 'discreet', 'wide']):
			task.visibility = vis
			for (t_ctx, q_ctx), expected in \
			TestContextAnalysis.relevancy_cases.items():
				task.context = t_ctx
				result = task.is_relevant_to_context(q_ctx)
				self.assertEqual(result, expected[i_vis])


class TestTasksSort(unittest.TestCase):

	# A list of correctly sorted tasks. The test consists in sorting them
	# and checking that the sorted list is the same as the original
	tasks = [
		Task(0, '', created=NOW, priority=3),
		Task(1, '', created=NOW-timedelta(minutes=1), priority=2),
		Task(2, '', created=NOW-timedelta(minutes=2), deadline=NOW+timedelta(days=3)),
		Task(3, '', created=NOW-timedelta(minutes=3), deadline=NOW+timedelta(days=4)),
		Task(4, '', created=NOW-timedelta(minutes=6), context='world'),
		Task(5, '', created=NOW-timedelta(minutes=7)),
		Task(6, '', created=NOW-timedelta(minutes=5), context='hello')
	]

	contexts = {'world': {'p': 2}}

	def test_task_sort(self):
		tasks_cpy = sorted(TestTasksSort.tasks,
			key=lambda t: t.order_infos(TestTasksSort.contexts))
		self.assertEqual(tasks_cpy, TestTasksSort.tasks)


class TestDispatch(unittest.TestCase):

	cases = {
		'': [('show', {'context': ''})],
		'ctx hello': [('show', {'context': 'hello'})],
		'add hello': [('add_task', {'content': 'hello'})],
		'task 1 -p 3': [('get_task_by_id', {'id_': '1'}),
			('apply_mutator', {'mutator': 'priority', 'value': 3})],
		'done 1': [('get_task_by_id', {'id_': '1'}),
			('set_done', {})],
		'ctx hello -p 2': [('apply_context_mutator', {'context': 'hello',
			'mutator': 'priority', 'value': 2})]
	}

	todolist = todo.TodoList([Task(id_=1, content='')], {})

	def test_dispatch(self):
		for line, sequence in TestDispatch.cases.items():
			argv = line.split()
			args, report = todo.parse_args(argv)
			self.assertIsNone(report)
			calls = []
			handler = utils.get_trace_handler(calls)
			sys.settrace(handler)
			todo.dispatch(args, TestDispatch.todolist)
			sys.settrace(None)
			calls = calls[1:]
			for (name, args), (e_name, e_args) in zip(sequence, calls):
				self.assertEqual(name, e_name)
				for arg_name, arg_value in args.items():
					self.assertIn(arg_name, e_args)
					self.assertEqual(arg_value, e_args[arg_name])


def test_trace():
	data_loc = todo.DATA_LOCATION
	is_loc = op.exists(data_loc)
	if is_loc:
		backup_path = data_loc + '-backup-' + str(NOW.timestamp)
		shutil.copy(data_loc, backup_path)
		os.remove(data_loc)
	try:
		utils.test_trace('tests/cmd_trace', todo.get_datetime)
	finally:
		if is_loc:
			shutil.copy(backup_path, data_loc)
			os.remove(backup_path)


if __name__ == '__main__':
	print('* Unit and integration tests')
	unittest.main(buffer=True, exit=False)
	print('* Fonctional tests')
	test_trace()
	print('OK')

import unittest, sys
import os.path as op
from datetime import timedelta


sys.path.insert(1, op.abspath('./todo'))

import todo.todo as todo
from todo.todo import Task, Context

NOW = todo.NOW


ROOT_CTX = Context('', None)
SUB1 = Context('subcontext1', ROOT_CTX)
SUB2 = Context('subcontext2', ROOT_CTX)
GRAND = Context('grandchild', SUB1)
ANOTHER = Context('another', GRAND)

GRAND.children = {'another': ANOTHER}
SUB1.children = {'grandchild': GRAND}
ROOT_CTX.children = {'subcontext1': SUB1, 'subcontext2': SUB2}


class TestContextStuff():

	def run_test(self, method_name):
		for args, expected in self.cases:
			result = getattr(Context, method_name)(*args)
			self.assertEqual(result, expected)


class TestContextPath(TestContextStuff, unittest.TestCase):

	cases = [
		((ROOT_CTX,), ''),
		((SUB1,), 'subcontext1'),
		((SUB2,), 'subcontext2'),
		((GRAND,), 'subcontext1.grandchild'),
		((ANOTHER,), 'subcontext1.grandchild.another')
	]

	def test_context_path(self):
		self.run_test('__str__')


class TestContextPathFrom(TestContextStuff, unittest.TestCase):

	cases = [
		((ROOT_CTX, ROOT_CTX), ''),
		((ANOTHER, ROOT_CTX), 'subcontext1.grandchild.another'),
		((ANOTHER, ANOTHER), ''),
		((ANOTHER, GRAND), 'another'),
		((SUB1, ROOT_CTX), 'subcontext1'),
		((SUB2, ROOT_CTX), 'subcontext2')
	]

	def test_context_path(self):
		self.run_test('path_from')


class TestGetContext(TestContextStuff, unittest.TestCase):

	cases = [
		((ROOT_CTX, ''), ROOT_CTX),
		((ROOT_CTX, 'subcontext1'), SUB1),
		((ROOT_CTX, 'subcontext2'), SUB2),
		((ROOT_CTX, 'subcontext1.grandchild.another'), ANOTHER),
		((GRAND, ''), GRAND),
		((GRAND, 'another'), ANOTHER)
	]

	def test_get_context(self):
		self.run_test('get_context')


class TestAddContext(unittest.TestCase):

	def test_add_already_existing_context(self):
		ctx = ROOT_CTX.add_contexts('subcontext2')
		self.assertEqual(ctx, SUB2)

	def test_add_leaf_context(self):
		ctx = ROOT_CTX.add_contexts('subcontext2.new')
		self.assertEqual(ctx, SUB2.children['new'])

	def test_add_multiple_contexts(self):
		ctx = ROOT_CTX.add_contexts('hello.world')
		self.assertEqual(ctx, ROOT_CTX.children['hello'].children['world'])


class TestContextAnalysis(unittest.TestCase):

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

#! /usr/bin/env python3

import argparse, json, os, re, sys
import os.path as op
from datetime import datetime, timezone, timedelta

# We check for the .dev file whose existence indicates that
# the datafile to use is ~/.doduh/data2.json instead of
# ~/.toduh/data.json
project_path = op.dirname(__file__)
dev_flag = op.join(project_path, '.dev')
if op.exists(dev_flag) and op.isfile(dev_flag):
	DATA_LOCATION = op.expanduser('~/.toduh/data2.json')
else:
	DATA_LOCATION = op.expanduser('~/.toduh/data.json')

NOW = datetime.utcnow().replace(tzinfo=timezone.utc)
INF = datetime.max.replace(tzinfo=timezone.utc)
LONG_AGO = datetime.min.replace(tzinfo=timezone.utc)
ISO_DATE = '%Y-%m-%dT%H:%M:%SZ'
USER_DATE_FORMATS = [
	'%Y-%m-%d',
	'%Y-%m-%dT%H:%M:%S',
]

REMAINING = {
	'w': 7*24*3600,
	'd': 24*3600,
	'h': 3600,
	'm': 60,
	's': 1
}
REMAINING_RE = re.compile('\A([0-9]+)([wdhms])\Z')

# Icons used to print tasks' properties in the terminal.
# True is the ASCII version for challenged terminals.
# False is the Unicode version.
CONTEXT_ICON = {True: '#', False: '#'}
TIME_ICON = {True: '~', False: '⌛'}
PRIORITY_ICON = {True: '!', False: '★'}


class Task:

	mutators = ['priority', 'deadline', 'start', 'context', 'visibility']
	fast_serial = ['id_', 'content', 'done', 'priority', 'context',
		'visibility']
	date_serial = ['created', 'deadline', 'start']
	defaults = {
		'created': LONG_AGO,
		'priority': 1,
		'deadline': INF,
		'start': NOW,
		'context': '',
		'done': False,
		'visibility': 'discreet'
	}

	def __init__(self, id_, content, **kwargs):
		self.id_ = id_
		self.content = content
		for key, val in kwargs.items():
			setattr(self, key, val)
		for key, val in Task.defaults.items():
			if not hasattr(self, key):
				setattr(self, key, val)
		self.remaining = self.deadline - NOW

	def apply_mutator(self, mutator, value):
		if mutator == 'priority':
			self.priority = value
		elif mutator == 'deadline':
			dt = get_datetime(value)
			if dt is None:
				raise ValueError('Invalid time format')
			else:
				self.deadline = dt
		elif mutator == 'start':
			dt = get_datetime(value)
			if dt is None:
				raise ValueError('Invalid time format')
			else:
				self.start = dt
		elif mutator == 'context':
			self.context = value
		elif mutator == 'visibility':
			self.visibility = value

	def set_done(self):
		self.done = True

	def get_dict(self):
		skelet = {}
		for p in Task.fast_serial:
			if p in self.__dict__ and not self.is_default(p):
				skelet[p] = self.__dict__[p]
		for p in Task.date_serial:
			if p in self.__dict__ and not self.is_default(p):
				skelet[p] = self.__dict__[p].strftime(ISO_DATE)
		return skelet

	def is_default(self, p):
		return p in Task.defaults and self.__dict__[p] == Task.defaults[p]

	def has_started(self):
		return NOW >= self.start

	def order_infos(self, contexts):
		if self.context in contexts and 'p' in contexts[self.context]:
			contextP = contexts[self.context]['p']
		else:
			contextP = 1
		return (-self.priority, self.remaining, -contextP, self.created)

	def is_relevant_to_context(self, context):
		if self.context == context:
			return True
		my_namespaces = get_namespaces(self.context)
		their_namespaces = get_namespaces(context)
		len_theirs = len(their_namespaces)
		if len_theirs != 0:
			descendant = my_namespaces[:len_theirs] == their_namespaces
		else:
			descendant = len(my_namespaces) == 1
		if self.visibility == 'hidden':
			return self.context == context
		elif self.visibility == 'discreet':
			return descendant
		elif self.visibility == 'wide':
			return descendant or context == ''

	def get_string(self, id_width, ascii_=False):
		string = '{id_:>{width}} | {content}'.format(id_=hex(self.id_)[2:],
			width=id_width, content=self.content)
		if self.context != '':
			string += ' {}{}'.format(CONTEXT_ICON[ascii_], self.context)
		if self.deadline != INF:
			user_friendly = parse_remaining(self.remaining)
			string += ' {} {} remaining'.format(TIME_ICON[ascii_], user_friendly)
		if self.priority != 1:
			string += ' {}{}'.format(PRIORITY_ICON[ascii_], self.priority)
		return string


class TodoList:

	context_mutators = ['visibility', 'priority']

	def __init__(self, tasks, contexts, id_width=None):
		# id_width is the width of the hexa representation of the task's
		# ID. It can be optionaly given to us so that we don't have to
		# iterate over the tasks ourselves. In this, it's computed by
		# import_data when it iterates over the tasks
		if id_width is not None:
			self.id_width = id_width
		else:
			self.id_width = max(len(hex(t.id_)) - 2 for t in tasks)
		self.tasks = tasks
		self.contexts = contexts

	def get_task_by_id(self, id_):
		actual_id = int(id_, 16)
		for task in self.tasks:
			if task.id_ == actual_id:
				return task

	def add_task(self, content, created):
		id_ = self.get_next_id()
		task = Task(id_, content, created=created)
		self.tasks.append(task)
		return task

	def apply_context_mutator(self, context, mutator, value):
		if mutator == 'priority':
			if context in self.contexts:
				self.contexts[context]['p'] = value
			else:
				self.contexts[context] = {'p': value}
		elif mutator == 'visibility':
			for task in self.tasks:
				if task.context == context:
					task.visibility = value
			if context in self.contexts:
				self.contexts[context]['v'] = value
			else:
				self.contexts[context] = {'v': value}

	def get_next_id(self):
		max_ = 0
		for task in self.tasks:
			id_ = task.id_
			if id_ > max_:
				max_ = id_
		return max_ + 1

	def show(self, context=''):
		for task in sorted(self.tasks,
			key=lambda t: t.order_infos(self.contexts)):
			if not task.done and task.is_relevant_to_context(context) and \
			task.has_started():
				try:
					print(task.get_string(self.id_width + 1))
				except UnicodeEncodeError:
					print(task.get_string(self.id_width + 1, ascii_=True))

	def save(self, location):
		if not op.exists(location):
			create_data_dir(location)
		with open(location, 'w', encoding='utf8') as data_f:
			data = {'tasks': [], 'contexts': self.contexts}
			for task in self.tasks:
				data['tasks'].append(task.get_dict())
			json.dump(data, data_f, sort_keys=True, indent=4,
				ensure_ascii=False)


def create_data_dir(data_location):
	dirname = op.dirname(data_location)
	if not op.exists(dirname):
		os.makedirs(dirname)


def get_datetime(string):
	match = REMAINING_RE.match(string)
	if match is not None:
		value, unit = match.groups()
		seconds = int(value) * REMAINING[unit]
		return NOW + timedelta(seconds=seconds)
	else:
		dt = None
		for pattern in USER_DATE_FORMATS:
			try:
				dt = datetime.strptime(string, pattern)
			except ValueError:
				continue
			else:
				dt = datetime.utcfromtimestamp(dt.timestamp())
				dt = dt.replace(tzinfo=timezone.utc)
				break
		return dt


def parse_remaining(delta):
	seconds = 3600 * 24 * delta.days + delta.seconds
	if seconds >= 2 * 24 * 3600:
		return '{} days'.format(delta.days)
	if seconds >= 2*3600:
		return '{} hours'.format(24*delta.days + delta.seconds // 3600)
	if seconds >= 2*60:
		return '{} minutes'.format(seconds // 60)
	return '{} seconds'.format(seconds)


def get_namespaces(context):
	splat = context.split('.')
	if splat == ['']:
		splat = []
	return splat


def import_data(data_location):
	if not op.exists(data_location):
		data = {'tasks': [], 'contexts': {}}
	else:
		with open(data_location, encoding='utf8') as todo_f:
			data = json.load(todo_f)
	contexts = data['contexts']
	tasks = []
	max_width = 0
	for dico in data['tasks']:
		if 'done' in dico and dico['done']:
			continue
		for key, val in dico.items():
			if key in Task.date_serial:
				dt = datetime.strptime(val, ISO_DATE)
				dt = dt.replace(tzinfo=timezone.utc)
				dico[key] = dt
		if 'visibility' not in dico:
			if 'context' in dico and dico['context'] in contexts and \
			'v' in contexts[dico['context']]:
				dico['visibility'] = contexts[dico['context']]['v']
		id_width = len(hex(dico['id_'])) - 2 # 0x...
		if id_width > max_width:
			max_width = id_width
		tasks.append(Task(**dico))
	return tasks, contexts, max_width


def dispatch(args, todolist):
	change = True
	if args.add is not None or args.task is not None:
	# Task Edition
		if args.add is not None:
		# Task Creation
			task = todolist.add_task(args.add, NOW)
		elif args.task is not None:
		# Task Selection
			task = todolist.get_task_by_id(args.task)
		if task is None:
			print('Task not found')
			return False
		values = vars(args)
		for mutator in Task.mutators:
			if values.get(mutator) is not None:
				task.apply_mutator(mutator, values[mutator])
	elif args.done is not None:
	# Task ending
		task = todolist.get_task_by_id(args.done)
		task.set_done()
	elif args.context is not None:
	# Other context related commands
		changed_something = False
		values = vars(args)
		for mutator in TodoList.context_mutators:
			if values.get(mutator) is not None:
				todolist.apply_context_mutator(args.context, mutator,
					values[mutator])
				changed_something = True
		if not changed_something:
			change = False
			todolist.show(args.context)
	else:
		change = False
		todolist.show()
	return change


def parse_args(argv):
	parser = argparse.ArgumentParser(description='CLI todo list manager')
	parser.add_argument('-a', '--add',
		help="Add a task to the todo list")
	parser.add_argument('--deadline',
		help="Set the deadline of the task")
	parser.add_argument('-s', '--start',
		help="Set the date before which the task's remaining time will "
		"be considered to be infinite")
	parser.add_argument('-c', '--context',
		help="Set the context of a task")
	parser.add_argument('-p', '--priority', type=int,
		help="Set the priority of a task or a context")
	parser.add_argument('-d', '--done',
		help="Set a task as done")
	parser.add_argument('-t', '--task',
		help="Select a task to alter")
	parser.add_argument('-v', '--visibility', choices=['hidden', 'discreet',
		'wide'],
		help="Set the visibility of a task: 'hidden', 'discreet' or 'wide'.")
	args = parser.parse_args(argv)
	return args


def main():
	tasks, contexts, id_width = import_data(DATA_LOCATION)
	todolist = TodoList(tasks, contexts, id_width)

	args = parse_args(sys.argv[1:])
	change = dispatch(args, todolist)
	if change:
		todolist.save(DATA_LOCATION)


if __name__ == '__main__':
	main()

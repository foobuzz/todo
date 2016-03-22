#! /usr/bin/env python3

"""todo. CLI todo list manager.

Usage:
  todo
  todo add <content> [--deadline MOMENT] [--start MOMENT] [--context CONTEXT]
    [--priority PRIORITY] [--visibility VISIBILITY]
  todo done <id>
  todo task <id> [--deadline MOMENT] [--start MOMENT] [--context CONTEXT]
    [--priority PRIORITY] [--visibility VISIBILITY]
  todo rm <id>
  todo ctx <context> [--priority PRIORITY] [--visibility VISIBILITY]
  todo contexts
  todo history
  todo purge
  todo help

Options:
  -d MOMENT, --deadline MOMENT            Set the deadline of a task
  -s MOMENT, --start MOMENT               Set the start-line of a task
  -c CONTEXT, --context CONTEXT           Set the context of a task
  -p INTEGER, --priority INTEGER          Set the priority of a task, or of a
                                          context
  -v VISIBILITY, --visibility VISIBILITY  Set the visibility of a task, or of a
                                          context.

"""

import json, os, re, sys
import os.path as op
from datetime import datetime, timezone, timedelta

from docopt import docopt

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
		setattr(self, mutator, value)

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
	if args['add'] or args['task']:
	# Task edition
		if args['add']:
		# Task creation
			task = todolist.add_task(args['<content>'], NOW)
		elif args['task']:
		# Task selection
			task = todolist.get_task_by_id(args['<id>'])
		if task is None:
			print('Task not found')
			return False
		for mutator in Task.mutators:
			option = '--'+mutator
			if args.get(option) is not None:
				task.apply_mutator(mutator, args[option])
	elif args['done']:
	# Task ending
		task = todolist.get_task_by_id(args['<id>'])
		task.set_done()
	elif args['rm']:
	# Task deletion
		print('Not implemented yet.')
	elif args['ctx']:
	# Other context related commands
		changed_something = False
		ctx = args['<context>']
		for mutator in TodoList.context_mutators:
			option = '--'+mutator
			if args.get(option) is not None:
				todolist.apply_context_mutator(ctx, mutator, args[option])
				changed_something = True
		if not changed_something:
			change = False
			todolist.show(args['<context>'])
	elif args['contexts']:
		print('Not implemented yet.')
	elif args['history']:
		print('Not implemented yet.')
	elif args['purge']:
		print('Not implemented yet.')
	elif args['help']:
		print(__doc__)
	else:
		change = False
		todolist.show()
	return change


def parse_args(argv):
	args = docopt(__doc__, argv=argv, help=False, version='2')
	report = None
	if args['--priority'] is not None:
		try:
			args['--priority'] = int(args['--priority'])
		except ValueError:
			report = 'PRIORITY must be an integer'
	if args['--visibility'] is not None:
		if args['--visibility'] not in ['discreet', 'wide', 'hidden']:
			report = "VISIBILITY must be one of the following: discreet, "+\
			"wide or hidden"
	for arg in ['--deadline', '--start']:
		if args[arg] is not None:
			dt = get_datetime(args[arg])
			if dt is None:
				report = "MOMENT must be in the YYYY-MM-DD format, or the "+\
				"YYYY-MM-DDTHH:MM:SS format, or a delay in the "+\
				"([0-9]+)([wdhms]) format"
			else:
				args[arg] = dt
	return args, report


def main():
	tasks, contexts, id_width = import_data(DATA_LOCATION)
	todolist = TodoList(tasks, contexts, id_width)

	args, report = parse_args(sys.argv[1:])
	if report is not None:
		print(report)
	else:
		change = dispatch(args, todolist)
		if change:
			todolist.save(DATA_LOCATION)


if __name__ == '__main__':
	main()

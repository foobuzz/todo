#! /usr/bin/env python3

"""todo. CLI todo list manager.

Usage:
  todo [<context>]
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
  todo --help
  todo --version
  todo --location

Options:
  -d MOMENT, --deadline MOMENT            Set the deadline of a task
  -s MOMENT, --start MOMENT               Set the start-line of a task
  -c CONTEXT, --context CONTEXT           Set the context of a task
  -p INTEGER, --priority INTEGER          Set the priority of a task, or of a
                                          context
  -v VISIBILITY, --visibility VISIBILITY  Set the visibility of a task, or of a
                                          context.

"""

import json, os, sys, shutil
import os.path as op
from datetime import datetime, timezone

from docopt import docopt

sys.path.insert(0, op.abspath(op.dirname(__file__)))
import utils

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

# Icons used to print tasks' properties in the terminal.
# True is the ASCII version for challenged terminals.
# False is the Unicode version.
CONTEXT_ICON = {True: '#', False: '#'}
TIME_ICON = {True: '~', False: '⌛'}
PRIORITY_ICON = {True: '!', False: '★'}

WIDE_HIST_THRESHOLD = 120


class HasDefaults:

	def init_defaults(self):
		for key, val in self.__class__.defaults.items():
			if not hasattr(self, key):
				setattr(self, key, val)

	def is_default(self, p):
		class_ = self.__class__
		defaults = class_.defaults
		return p in defaults and self.__dict__[p] == class_.defaults[p]

	def apply_mutator(self, mutator, value):
		setattr(self, mutator, value)


class Context(HasDefaults):

	mutators = ['visibility', 'priority']
	defaults = {
		'visibility': 'discreet',
		'priority': 1
	}

	def __init__(self, name, visibility=None, priority=None):
		self.name = name
		if visibility is not None:
			self.visibility = visibility
		if priority is not None:
			self.priority = priority
		self.init_defaults()
		self.namespace = self.get_namespace()
		self.population = 0

	def __eq__(self, other):
		return self.name == other.name

	def __str__(self):
		return self.name

	def get_namespace(self):
		splat = self.name.split('.')
		if splat == ['']:
			splat = []
		return splat

	def is_subcontext(self, other):
		my_namespaces = self.namespace
		their_namespaces = other.namespace
		len_theirs = len(their_namespaces)
		if len_theirs != 0:
			descendant = my_namespaces[:len_theirs] == their_namespaces
		else:
			descendant = len(my_namespaces) == 1
		return descendant

	def get_dict(self):
		skelet = {}
		if not self.is_default('visibility'):
			skelet['v'] = self.visibility
		if not self.is_default('priority'):
			skelet['p'] = self.priority
		return skelet


EMPTY_CONTEXT = Context('')


class Task(HasDefaults):

	mutators = ['priority', 'deadline', 'start', 'context', 'visibility']
	fast_serial = ['id_', 'content', 'done', 'priority', 'visibility']
	date_serial = ['created', 'deadline', 'start']
	defaults = {
		'created': LONG_AGO,
		'priority': 1,
		'deadline': INF,
		'start': NOW,
		'context': EMPTY_CONTEXT,
		'done': False,
		'visibility': 'discreet'
	}

	def __init__(self, id_, content, **kwargs):
		self.id_ = id_
		self.content = content
		for key, val in kwargs.items():
			setattr(self, key, val)
		self.init_defaults()
		self.remaining = self.deadline - NOW

	def get_visibility(self):
		if self.is_default('visibility'):
			return self.context.visibility
		else:
			return self.visibility

	def set_done(self):
		self.done = True

	def get_dict(self):
		skelet = {}
		for p in Task.fast_serial:
			if p in self.__dict__ and not self.is_default(p):
				skelet[p] = self.__dict__[p]
		for p in Task.date_serial:
			if p in self.__dict__ and not self.is_default(p):
				skelet[p] = self.__dict__[p].strftime(utils.ISO_DATE)
		if not self.is_default('context'):
			skelet['context'] = self.context.name
		return skelet

	def has_started(self):
		return NOW >= self.start

	def order_infos(self):
		return (-self.priority,
			self.remaining,
			-self.context.priority,
			self.created)

	def is_relevant_to_context(self, context):
		if self.context == context:
			return True
		descendant = self.context.is_subcontext(context)
		if self.get_visibility() == 'hidden':
			return self.context == context
		elif self.get_visibility() == 'discreet':
			return descendant
		elif self.get_visibility() == 'wide':
			return descendant or context == EMPTY_CONTEXT

	def get_string(self, id_width, ascii_=False):
		string = '{id_:>{width}} | {content}'.format(id_=hex(self.id_)[2:],
			width=id_width, content=self.content)
		if not self.is_default('context'):
			string += ' {}{}'.format(CONTEXT_ICON[ascii_], self.context)
		if not self.is_default('deadline'):
			user_friendly = utils.parse_remaining(self.remaining)
			string += ' {} {} remaining'.format(TIME_ICON[ascii_], user_friendly)
		if not self.is_default('priority'):
			string += ' {}{}'.format(PRIORITY_ICON[ascii_], self.priority)
		return string


class TodoList:

	def __init__(self, tasks, contexts, id_width=None):
		# id_width is the width of the hexa representation of the task's ID. It
		# can be optionaly given to us so that we don't have to iterate over
		# the tasks ourselves. In this case, it's computed by import_data when
		# it iterates over the tasks
		if id_width is not None:
			self.id_width = id_width
		else:
			self.id_width = max(len(hex(t.id_)) - 2 for t in tasks)
		self.tasks = tasks
		self.contexts = contexts

	def get_task(self, id_):
		for task in self.tasks:
			if task.id_ == id_:
				return task

	def add_task(self, content, created):
		id_ = self.get_next_id()
		task = Task(id_, content, created=created)
		self.tasks.append(task)
		return task

	def remove_task(self, id_):
		self.tasks = [t for t in self.tasks if t.id_ != id_]

	def purge(self):
		self.tasks = [t for t in self.tasks if not t.done]

	def __iter__(self):
		return iter(self.tasks)

	def get_next_id(self):
		max_ = 0
		for task in self.tasks:
			id_ = task.id_
			if id_ > max_:
				max_ = id_
		return max_ + 1

	def show(self, context=EMPTY_CONTEXT):
		for task in sorted(self.tasks, key=lambda t: t.order_infos()):
			if not task.done and task.is_relevant_to_context(context) and \
			task.has_started():
				try:
					print(task.get_string(self.id_width + 1))
				except UnicodeEncodeError:
					print(task.get_string(self.id_width + 1, ascii_=True))

	def show_history(self):
		term_width = shutil.get_terminal_size().columns
		id_width = max(2, self.id_width) + 1
		struct = utils.get_history_struct(id_width,
			term_width > WIDE_HIST_THRESHOLD)
		utils.print_table(struct, self.tasks, term_width)

	def show_contexts(self):
		contexts = list(self.contexts.values())
		contexts.sort(key=lambda c: c.name)
		struct = [
			('context', lambda a: a, '<', 'name', lambda a: a),
			('visibility', 10, '<', 'visibility', lambda a: a),
			('priority', 8, '<', 'priority', lambda a: str(a)),
			('undone tasks', 12, '<', 'population', lambda a: str(a))
		]
		utils.print_table(struct, contexts, 80)

	def save(self, location):
		if not op.exists(location):
			create_data_dir(location)
		contexts = {}
		for name, ctx in self.contexts.items():
			dict_ = ctx.get_dict()
			if len(dict_) > 0:
				contexts[name] = dict_
		data = {'tasks': [], 'contexts': contexts}
		for task in self.tasks:
			data['tasks'].append(task.get_dict())
		with open(location, 'w', encoding='utf8') as data_f:
			json.dump(data, data_f, sort_keys=True, indent=4,
				ensure_ascii=False)


def create_data_dir(data_location):
	dirname = op.dirname(data_location)
	if not op.exists(dirname):
		os.makedirs(dirname)


def import_data(data_location):
	"""Import the tasks from file whose path is data_location.

	Once the JSON data is loaded, stuff is converted into proper objects. This
	includes:
	 - Conversion of datetime strings to datetime objects
	 - Conversion of context strings to context objects
	 - Conversion of a task's dictionary to a task object

	Returns: a 3-tuple containing:
	 - The list of tasks
	 - A dictionary which is the "contexts table". This dictionary associates
       context's strings to their corresponding context object.
	 - The maximum width of a task's ID in hexadecimal representation. This is
       used to know how to format the todo list when printing. This kind of
       information should be retrieved at importing to avoid further passes on
       the list of tasks."""
	if not op.exists(data_location):
		data = {'tasks': [], 'contexts': {}}
	else:
		with open(data_location, encoding='utf8') as todo_f:
			data = json.load(todo_f)
	contexts = {'': EMPTY_CONTEXT}
	for name, infos in data['contexts'].items():
		contexts[name] = Context(name, infos.get('v'), infos.get('p'))
	tasks = []
	max_width = 0
	for dico in data['tasks']:
		for key, val in dico.items():
			if key in Task.date_serial:
				dt = datetime.strptime(val, utils.ISO_DATE)
				dt = dt.replace(tzinfo=timezone.utc)
				dico[key] = dt
		if 'context' in dico:
			ctx_name = dico['context']
			if ctx_name in contexts:
				ctx = contexts[ctx_name]
				dico['context'] = ctx
			else:
				ctx = Context(ctx_name)
				dico['context'] = ctx
				contexts[ctx_name] = ctx
		else:
			ctx = EMPTY_CONTEXT
			# Let's remember that we manipulate the same EMPTY_CONTEXT object
			# in the whole program. So in this case the ctx variable does
			# reference the object in the contexts dict
		if 'done' not in dico or not dico['done']:
			ctx.population += 1
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
			task = todolist.get_task(args['<id>'])
		if task is None:
			print('Task not found')
			return False
		for mutator in Task.mutators:
			option = '--'+mutator
			if args.get(option) is not None:
				task.apply_mutator(mutator, args[option])
	elif args['done']:
		task = todolist.get_task(args['<id>'])
		task.set_done()
	elif args['rm']:
		todolist.remove_task(args['<id>'])
	elif args['ctx']:
		changed_something = False
		ctx = args['<context>']
		for mutator in Context.mutators:
			option = '--'+mutator
			if args.get(option) is not None:
				ctx.apply_mutator(mutator, args[option])
				changed_something = True
		if not changed_something:
			change = False
			todolist.show(ctx)
	elif args['contexts']:
		todolist.show_contexts()
	elif args['history']:
		todolist.show_history()
	elif args['purge']:
		todolist.purge()
	else:
		change = False
		ctx = args['<context>']
		if ctx is None:
			ctx = EMPTY_CONTEXT
		todolist.show(ctx)
	return change


def parse_args(args, contexts):
	"""Parse the args dictionary returned by docopt.

	Strings are converted into proper objects. For example, datetime related
	strings are converted into datetime objects, hexadecimal task's
	identifiers are converted to integer and context names are converted into
	context objects. The `contexts` argument is the contexts table used to
	retrieve contexts thanks to their names

	If one of the conversion fails, a report is written about the fail. This
	report is None if no failure has been encountered. The report is returned
	by the function"""
	# The command-line interface is ambiguous. There is `todo [<context>]` to
	# only show the tasks of a specific context. There's also all other
	# commands such as `todo history`. The desired behavior is that an
	# existing command always wins over a context's name. If a user has a
	# context which happens to have the name of a command, he can still do
	# `todo ctx history` for example.

	# docopt has no problem making a command win over a context's name *if
	# there are parameters or option accompanying the command*. This means
	# that for parameters-free commands such as `todo history`, docopt thinks
	# that it's `todo <context>` with <context> = 'history'. To make up for
	# such behavior, what I do is that I look if there's a <context> value
	# given for a command which doesn't accept context, this context value
	# being the name of a command. In such case, I set the corresponding
	# command flag to True and the context value to None. Actually, the only
	# command accepting a context value is `ctx`.
	if not args['ctx'] and args['<context>'] in {'contexts', 'history',
	'purge'}:
		args[args['<context>']] = True
		args['<context>'] = None
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
			dt = utils.get_datetime(args[arg], NOW)
			if dt is None:
				report = "MOMENT must be in the YYYY-MM-DD format, or the "+\
				"YYYY-MM-DDTHH:MM:SS format, or a delay in the "+\
				"([0-9]+)([wdhms]) format"
			else:
				args[arg] = dt
	if args['<id>'] is not None:
		try:
			args['<id>'] = int(args['<id>'], 16)
		except ValueError:
			report = "Invalid task ID"
	for arg in ['--context', '<context>']:
		if args[arg] is not None:
			ctx = contexts.get(args[arg])
			if ctx is None:
				ctx = Context(args[arg])
				contexts[args[arg]] = ctx
			args[arg] = ctx
	return report


def main():
	argv = sys.argv[1:]
	if len(argv) == 1 and argv[0] == 'doduh':
		print('Beethoven - Symphony No. 5')
		sys.exit(0)
	args = docopt(__doc__, argv=argv, help=False, version='2')

	if args['--help']:
		print(__doc__)
	elif args['--version']:
		print('2')
	elif args['--location']:
		print(DATA_LOCATION)
	else:
		tasks, contexts, id_width = import_data(DATA_LOCATION)
		todolist = TodoList(tasks, contexts, id_width)

		report = parse_args(args, contexts)
		if report is not None:
			print(report)
		else:
			change = dispatch(args, todolist)
			if change:
				todolist.save(DATA_LOCATION)


if __name__ == '__main__':
	main()

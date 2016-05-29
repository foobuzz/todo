#! /usr/bin/env python3

"""todo. CLI todo list manager.

Usage:
  todo [<context>]
  todo add <content> [--deadline MOMENT] [--start MOMENT] [--context CONTEXT]
    [--priority PRIORITY] [--visibility VISIBILITY]
  todo done <id>...
  todo task <id> [--deadline MOMENT] [--start MOMENT] [--context CONTEXT]
    [--priority PRIORITY] [--visibility VISIBILITY] [--text CONTENT]
  todo edit <id>
  todo rm <id>...
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
  -t CONTENT, --text CONTENT              Set the text of a task
  -v VISIBILITY, --visibility VISIBILITY  Set the visibility of a task, or of a
                                          context.

"""

import json, os, sys, shutil
import os.path as op
from datetime import datetime, timezone
from collections import OrderedDict, abc

from docopt import docopt

import utils
from rainbow import ColoredStr
from config import DATA_LOCATION, CONFIG


SHOW_AFTER = utils.parse_list(CONFIG.get('App', 'show_after'))

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
		class_ = self.__class__
		if hasattr(class_, 'bindings') and mutator in class_.bindings:
			attr = class_.bindings[mutator]
		else:
			attr = mutator
		setattr(self, attr, value)


class Context(HasDefaults):

	mutators = ['visibility', 'priority']
	defaults = {
		'visibility': 'discreet',
		'priority': 1
	}

	def __init__(self, name, parent, visibility=None, priority=None):
		if '.' in name:
			raise Exception('Oh my god!')
		self.name = name
		self.parent = parent
		self.children = {}
		self.population = 0
		if parent is None:
			self.path = ''
		else:
			dot = parent != ROOT_CTX
			self.path = parent.path + '.'*dot + self.name
		if visibility is not None:
			self.visibility = visibility
		if priority is not None:
			self.priority = priority
		self.init_defaults()

	def __eq__(self, other):
		return self is other

	def __str__(self):
		return self.path

	def is_leaf(self):
		return len(self.children) == 0

	def is_subcontext(self, other):
		if self == other:
			return True
		for child in other.children.values():
			if child.is_leaf() and child == self:
				return True
			if not child.is_leaf():
				if self.is_subcontext(child):
					return True
		return False

	def get_population(self):
		children = sum(c.get_population() for c in self.children.values())
		return self.population + children

	def get_context(self, path):
		if path == '':
			return self
		components = path.split('.')
		pointer = self
		for name in components:
			if name not in pointer.children:
				return None
			pointer = pointer.children[name]
		return pointer

	def add_contexts(self, path):
		if path == '':
			return self
		components = path.split('.')
		pointer = self
		for name in components:
			if name in pointer.children:
				pointer = pointer.children[name]
			else:
				new_ctx = Context(name, pointer)
				pointer.children[name] = new_ctx
				pointer = new_ctx
		return pointer

	def items(self):
		yield self.path, self
		for child in self.children.values():
			for item in child.items():
				yield item

	def show_contexts(self):
		paths = [i[1] for i in self.items()]
		paths.sort(key=lambda c: c.path)
		struct = [
			('context', lambda a: a, '<', 'path', lambda a: a),
			('visibility', 10, '<', 'visibility', lambda a: a),
			('priority', 8, '<', 'priority', lambda a: str(a)),
			('undone tasks', 12, '<', None, lambda a: str(a.get_population()))
		]
		utils.print_table(struct, paths, 80)

	def get_dict(self):
		skelet = {}
		if not self.is_default('visibility'):
			skelet['v'] = self.visibility
		if not self.is_default('priority'):
			skelet['p'] = self.priority
		return skelet


ROOT_CTX = Context('', None)


class Task(HasDefaults):

	mutators = ['priority', 'deadline', 'start', 'context', 'visibility',
		'text']
	# The look-up table to use to convert command-line arguments name to their
	# object attribute counterpart. Most arguments have the name of their
	# corresponding attribute, some others don't.
	bindings = {
		'text': 'content'
	}
	fast_serial = ['id_', 'content', 'done', 'priority', 'visibility']
	date_serial = ['created', 'deadline', 'start']
	defaults = {
		'created': LONG_AGO,
		'priority': 1,
		'deadline': INF,
		'start': NOW,
		'context': ROOT_CTX,
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

	def apply_mutator(self, mutator, value):
		if mutator == 'context':
			self.context = ROOT_CTX.add_contexts(value)
		else:
			super().apply_mutator(mutator, value)

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
			skelet['context'] = self.context.path
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
			if context == ROOT_CTX:
				return self.context.parent == ROOT_CTX
			else:
				return descendant
		elif self.get_visibility() == 'wide':
			return descendant or context == ROOT_CTX

	def get_string(self, id_width, ascii_=False):
		id_str = may_be_colored(hex(self.id_)[2:], CONFIG.get('Colors', 'id'))
		if isinstance(id_str, ColoredStr):
			ansi_offset = id_str.lenesc
		else:
			ansi_offset = 0
		content_str = may_be_colored(self.content, CONFIG.get('Colors', 'content'))
		string = '{id_:>{width}} | {content}'.format(
			id_=id_str,
			width=id_width + ansi_offset,
			content=content_str
		)
		if not self.is_default('context'):
			ctx_string = ' {}{}'.format(CONTEXT_ICON[ascii_], self.context)
			string += may_be_colored(ctx_string, CONFIG.get('Colors', 'context'))
		if not self.is_default('deadline'):
			user_friendly = utils.parse_remaining(self.remaining)
			remaining_str = ' {} {} remaining'.format(TIME_ICON[ascii_], user_friendly)
			string += may_be_colored(remaining_str, CONFIG.get('Colors', 'deadline'))
		if not self.is_default('priority'):
			prio_str = ' {}{}'.format(PRIORITY_ICON[ascii_], self.priority)
			string += may_be_colored(prio_str, CONFIG.get('Colors', 'priority'))
		return string


class TodoList(abc.MutableMapping):

	def __init__(self, tasks, id_width=None):
		# id_width is the width of the hexa representation of the task's ID. It
		# can be optionaly given to us so that we don't have to iterate over
		# the tasks ourselves. In this case, it's computed by import_data when
		# it iterates over the tasks
		if id_width is not None:
			self.id_width = id_width
		else:
			self.id_width = max(len(hex(t.id_)) - 2 for t in tasks)
		self.tasks = tasks

	def __getitem__(self, key):
		return self.tasks[key]

	def __setitem__(self, key, value):
		self.tasks[key] = value

	def __delitem__(self, key):
		del self.tasks[key]

	def __contains__(self, key):
		return key in self.tasks

	def __iter__(self):
		return self.tasks.__iter__()

	def __len__(self):
		return len(self.tasks)

	def keys(self):
		return self.__iter__()

	def add_task(self, content, created):
		if len(self.tasks) == 0:
			id_ = 1
		else:
			id_ = next(reversed(self.tasks)) + 1
		task = Task(id_, content, created=created)
		self[id_] = task
		return task

	def set_done(self, id_list):
		for id_ in id_list:
			self[id_].set_done()

	def remove_tasks(self, id_list):
		for id_ in id_list:
			del self[id_]

	def purge(self):
		to_rm = []
		# I prefer not to alter the dict I'm interating over
		for id_, task in self.items():
			if task.done:
				to_rm.append(id_)
		for id_ in to_rm:
			del self[id_]

	def show(self, path=''):
		context = ROOT_CTX.get_context(path)
		for task in sorted(self.tasks.values(), key=lambda t: t.order_infos()):
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
		utils.print_table(struct, self.tasks.values(), term_width)

	def save(self, location):
		if not op.exists(location):
			create_data_dir(location)
		contexts = {}
		for path, ctx in ROOT_CTX.items():
			dict_ = ctx.get_dict()
			if len(dict_) > 0:
				contexts[path] = dict_
		data = {'tasks': [], 'contexts': contexts}
		for task in self.tasks.values():
			data['tasks'].append(task.get_dict())
		with open(location, 'w', encoding='utf8') as data_f:
			json.dump(data, data_f, sort_keys=True, indent=4,
				ensure_ascii=False)


def may_be_colored(string, color):
	if CONFIG.getboolean('Colors', 'colors'):
		palette = CONFIG.get('Colors', 'palette')
		return ColoredStr(string, color, palette)
	else:
		return string


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
	if not op.exists(data_location) or op.getsize(data_location) == 0:
		data = {'tasks': [], 'contexts': {}}
	else:
		with open(data_location, encoding='utf8') as todo_f:
			data = json.load(todo_f)
	tasks = OrderedDict()
	max_width = 0
	for dico in data['tasks']:
		for key, val in dico.items():
			if key in Task.date_serial:
				dt = datetime.strptime(val, utils.ISO_DATE)
				dt = dt.replace(tzinfo=timezone.utc)
				dico[key] = dt
		if 'context' in dico:
			path = dico['context']
			ctx = ROOT_CTX.add_contexts(path)
		else:
			ctx = ROOT_CTX
		dico['context'] = ctx
		if 'done' not in dico or not dico['done']:
			ctx.population += 1
		id_width = len(hex(dico['id_'])) - 2 # 0x...
		if id_width > max_width:
			max_width = id_width
		tasks[dico['id_']] = Task(**dico)
	for path in data['contexts']:
		ctx = ROOT_CTX.add_contexts(path)
		if 'v' in data['contexts'][path]:
			ctx.visibility = data['contexts'][path]['v']
		if 'p' in data['contexts'][path]:
			ctx.priority = data['contexts'][path]['p']
	return tasks, max_width


def dispatch(args, todolist):
	change = True
	need_show = any(args[command] for command in SHOW_AFTER)
	show_ctx = None
	if args['add'] or args['task']:
	# Task edition
		if args['add']:
		# Task creation
			task = todolist.add_task(args['<content>'], NOW)
		elif args['task']:
		# Task selection
			task = todolist[args['<id>'][0]]
		if task is None:
			print('Task not found')
			return False
		for mutator in Task.mutators:
			option = '--'+mutator
			if args.get(option) is not None:
				task.apply_mutator(mutator, args[option])
	elif args['edit']:
		task = todolist[args['<id>'][0]]
		if task is None:
			print('Task not found')
			return False
		new_content = utils.input_from_editor(task.content)
		if new_content.endswith('\n'):
		# hurr durr I'm a text editor I append a newline at the end of files
			new_content = new_content[:-1]
		task.content = new_content
	elif args['done']:
		todolist.set_done(args['<id>'])
	elif args['rm']:
		todolist.remove_tasks(args['<id>'])
	elif args['ctx']:
		changed_something = False
		ctx = ROOT_CTX.add_contexts(args['<context>'])
		for mutator in Context.mutators:
			option = '--'+mutator
			if args.get(option) is not None:
				ctx.apply_mutator(mutator, args[option])
				changed_something = True
		if not changed_something:
			change = False
			todolist.show(args['<context>'])
	elif args['contexts']:
		ROOT_CTX.show_contexts()
	elif args['history']:
		todolist.show_history()
	elif args['purge']:
		todolist.purge()
	else:
		change = False
		need_show = True
		show_ctx = args['<context>']
	if need_show:
		if show_ctx is None:
			show_ctx = ''
		todolist.show(show_ctx)
	return change


def parse_args(args):
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
		for i in range(len(args['<id>'])):
		# I prefer not to directly iterate over the list since I'm going to
		# alter it
			id_ = args['<id>'][i]
			try:
				args['<id>'][i] = int(id_, 16)
			except ValueError:
				report = "Invalid task ID: {}".format(id_)
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
		# Parsing the command-line
		report = parse_args(args)
		if report is not None:
			print(report)
			sys.exit(1)

		# Importing the data
		tasks, id_width = import_data(DATA_LOCATION)

		todolist = TodoList(tasks, id_width)
		change = dispatch(args, todolist)
		if change:
			todolist.save(DATA_LOCATION)


if __name__ == '__main__':
	main()

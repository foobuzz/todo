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
  todo contexts [<context>]
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

import json, os, sys
import os.path as op
from datetime import datetime, timezone
from collections import OrderedDict, abc

from docopt import docopt

from . import utils
from .rainbow import ColoredStr
from .config import DATA_LOCATION, DATA_CTX, CONFIG


__version__ = '2.1'


COMMANDS = {'add', 'done', 'task', 'edit', 'rm', 'ctx', 'contexts', 'history',
	'purge'}

EMPTY_DATA = {
	'last_task': None,
	'last_context': None,
	'tasks': [],
	'contexts': {}
}

LAST = 'LAST'

TASK404 = 'Task not found.'
CTX404 = 'Context not found.'

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

	"""The tree of contexts. Each context has a name and its children are
	represented using a dictionary where the keys are the names of the
	children and the values are references to the children. Each context keeps
	a reference to its parent context. The root context is defined by having a
	None parent and, by conventation, has the empty string as name.

	The path of a context is represented using a dot to separate different
	contexts' name accross the tree, which means that a context's name cannot
	contain a dot. The dot leading from the root context to its children is
	skipped so that paths don't starts with a dot. The str representation of a
	context is its path.

	While this class represent any node in the tree, most of its method will
	be called on the root context, which might make recursive calls to
	subcontexts"""

	mutators = ['visibility', 'priority']
	defaults = {
		'visibility': 'discreet',
		'priority': 1
	}

	def __init__(self, name, parent, visibility=None, priority=None):
		assert '.' not in name
		self.name = name
		self.parent = parent
		self.children = {}
		self.population = 0
		if parent is None:
			self.path = ''
		else:
			dot = not parent.is_root()
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

	def path_from(self, context):
		"""Return the path leading to the context given an ancestor context.
		e.g. "watchlist.movies".path_from("watchlist") = "movies" (str
		representation used for convenience)"""
		pointer = self
		path = ''
		while pointer != context:
			path = '.' + pointer.name + path
			pointer = pointer.parent
		return path[1:] if len(path) > 0 else path

	def is_root(self):
		return self.parent is None

	def is_leaf(self):
		return len(self.children) == 0

	def is_subcontext(self, other):
		if self == other:
			return True
		for child in other.children.values():
			if child == self:
				return True
			if self.is_subcontext(child):
				return True
		return False

	def get_population(self):
		"""The population of a context is the number of tasks this context is
		associated to. Each context has a count of the number of tasks that
		references exactly this context. This methods also counts tasks
		associated to subcontexts."""
		children = sum(c.get_population() for c in self.children.values())
		return self.population + children

	def get_context(self, path):
		"""Search for the context having the given path. Most of the time will
		be called on the root context with an absolute path. Returns the found
		context, or None"""
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
		"""Add the context represented by the given path, creating all
		intermediary nessecary contexts. Returns the newly created context."""
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
		"""Iterates over the tuples (path, context) by doing a depth-first
		traversal over the tree."""
		yield self.path, self
		for child in self.children.values():
			for item in child.items():
				yield item

	def show_contexts(self):
		"""Pretty print all contexts and their properties."""
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
		"""Creates a dictionary for serialization."""
		skelet = {}
		if not self.is_default('visibility'):
			skelet['v'] = self.visibility
		if not self.is_default('priority'):
			skelet['p'] = self.priority
		return skelet


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
		'done': False,
		'visibility': 'discreet'
	}

	def __init__(self, id_, content, context, **kwargs):
		self.id_ = id_
		self.content = content
		self.context = context
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
			if context.is_root():
				return self.context.parent.is_root()
			else:
				return descendant
		elif self.get_visibility() == 'wide':
			return descendant or context.is_root()

	def get_string(self, id_width, from_context, ascii_=False):
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
		ctx_path = self.context.path_from(from_context)
		if ctx_path != '':
			ctx_string = ' {}{}'.format(CONTEXT_ICON[ascii_], ctx_path)
			string += may_be_colored(ctx_string, CONFIG.get('Colors', 'context'))
		if not self.is_default('deadline'):
			user_friendly = utils.parse_remaining(self.remaining)
			remaining_str = ' {} {} remaining'.format(TIME_ICON[ascii_], user_friendly)
			string += may_be_colored(remaining_str, CONFIG.get('Colors', 'deadline'))
		if not self.is_default('priority'):
			prio_str = ' {}{}'.format(PRIORITY_ICON[ascii_], self.priority)
			string += may_be_colored(prio_str, CONFIG.get('Colors', 'priority'))
		return string


def check_last(fallback):
	"""Return a decorator for a method of the TodoList which accepts an
	identifier as only explicit argument. The returned decorator alters the
	method so that LAST is accepted as an identifier, in which case the value
	corresponding to the identifier should be given by the attribute of the
	TodoList named `fallback`."""
	def decorator(function):
		def substitute(todolist, identifier):
			if identifier == LAST:
				identifier = getattr(todolist, fallback)
				if identifier is None:
					return None
			return function(todolist, identifier)
		return substitute
	return decorator


class TodoList(abc.MutableMapping):

	"""The TodoList supports the mapping protocol. Keys are tasks' ID and
	values are tasks themselves.

	Adding a new task should be done via the `add_task` method which takes
	care of finding the next available ID and building a new task from minimum
	requirements (content of the task and date of creation).

	The TodoList has a reference to a context tree via its `root_ctx`
	attribute. The tree should not be accessed itself but by methods defined
	in the TodoList to manipulate it.

	The special ID LAST can be used to retrieve the last referenced task
	(resp. context) of the TodoList (retrieved, added or modified), although
	the TodoList object itself does not support updating of the last
	referenced task (resp. context) upon calls on related methods; the manager
	of the TodoList should do it itself by updating the `last_task` (resp.
	`last_context`) attributes"""

	def __init__(self, context, tasks, id_width=None, last_task=None,
		last_context=None):
		# id_width is the width of the hexa representation of the task's ID. It
		# can be optionaly given to us so that we don't have to iterate over
		# the tasks ourselves. In this case, it's computed by import_data when
		# it iterates over the tasks
		self.root_ctx = context
		if id_width is not None:
			self.id_width = id_width
		else:
			self.id_width = max(len(hex(t.id_)) - 2 for t in tasks)
		self.tasks = tasks
		self.last_task = last_task
		self.last_context = last_context
		self.updated_last = False

	@check_last('last_task')
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

	@check_last('last_context')
	def get_context(self, path):
		return self.root_ctx.get_context(path)

	@check_last('last_context')
	def add_contexts(self, path):
		return self.root_ctx.add_contexts(path)

	def keys(self):
		return self.__iter__()

	def update_last_task(self, id_):
		if id_ != self.last_task:
			self.last_task = id_
			self.updated_last = True

	def update_last_context(self, path):
		if path != self.last_context:
			self.last_context = path
			self.updated_last = True

	def add_task(self, content, created):
		if len(self.tasks) == 0:
			id_ = 1
		else:
			id_ = next(reversed(self.tasks)) + 1
		task = Task(id_, content, self.root_ctx, created=created)
		self[id_] = task
		return task

	def set_done(self, id_list):
		task = None
		for id_ in id_list:
			task = self.get(id_, None)
			if task is not None:
				task.set_done()
		return task

	def remove_tasks(self, id_list):
		task = None
		for id_ in id_list:
			if id_ == LAST:
				id_ = self.last_task
			if id_ in self:
				task = self[id_]
				del self[id_]
		return task

	def purge(self):
		to_rm = []
		# I prefer not to alter the dict I'm interating over
		for id_, task in self.items():
			if task.done:
				to_rm.append(id_)
		for id_ in to_rm:
			del self[id_]

	def apply_task_mutator(self, id_, mutator, value):
		if mutator == 'context':
			ctx = self.add_contexts(value)
			self[id_].context = ctx
		else:
			self[id_].apply_mutator(mutator, value)

	def show(self, path=''):
		context = self.get_context(path)
		if context is None:
			return None
		for task in sorted(self.tasks.values(), key=lambda t: t.order_infos()):
			if not task.done and task.is_relevant_to_context(context) and \
			task.has_started():
				try:
					print(task.get_string(self.id_width + 1, context))
				except UnicodeEncodeError:
					print(task.get_string(self.id_width + 1, context, ascii_=True))
		return context

	def show_history(self):
		term_width = os.get_terminal_size().columns
		id_width = max(2, self.id_width) + 1
		struct = utils.get_history_struct(id_width,
			term_width > WIDE_HIST_THRESHOLD)
		utils.print_table(struct, self.tasks.values(), term_width)

	def save(self, location):
		contexts = {}
		with open(DATA_CTX, 'w') as ctx_file:
			for path, ctx in self.root_ctx.items():
				dict_ = ctx.get_dict()
				if len(dict_) > 0:
					contexts[path] = dict_
				ctx_file.write(path+'\n')
		data = {
			'tasks': [],
			'contexts': contexts,
			'last_task': self.last_task,
			'last_context': self.last_context
		}
		for task in self.tasks.values():
			data['tasks'].append(task.get_dict())
		save_data(data, location)


def may_be_colored(string, color):
	"""Return a string, colored or not, depending on the CONFIG variable"""
	if CONFIG.getboolean('Colors', 'colors'):
		palette = CONFIG.get('Colors', 'palette')
		return ColoredStr(string, color, palette)
	else:
		return string


def check_none(var, message):
	"""Return a boolean indicating whether `var` is None or not, and print the given `message` if it's None"""
	if var is None:
		print(message)
		return True
	return False


def open_data(data_location):
	"""Load the dictionary from the JSON file at `data_location`, or return
	todo specific empty data if the file doesn't exist"""
	if not op.exists(data_location) or op.getsize(data_location) == 0:
		data = EMPTY_DATA
	else:
		with open(data_location, encoding='utf8') as todo_f:
			data = json.load(todo_f)
	return data


def save_data(data, location):
	"""Save the object `data` to the file at `location` in JSON format. The
	file and the directories leading to it will be created if not already
	existing."""
	if not op.exists(location):
		create_data_dir(location)
	with open(location, 'w', encoding='utf8') as data_f:
		json.dump(data, data_f, sort_keys=True, indent=4,
			ensure_ascii=False)	


def create_data_dir(data_location):
	"""Creates the directory whose path is `data_location` if it doesn't
	already exist"""
	dirname = op.dirname(data_location)
	if not op.exists(dirname):
		os.makedirs(dirname)


def import_data(data):
	"""Build and return a TodoList object from the raw data found in `data`"""
	root_ctx = Context('', None)
	tasks = OrderedDict()
	max_width = 0
	for dico in data['tasks']:
		dtask = dico.copy()
		for key, val in dtask.items():
			if key in Task.date_serial:
				dt = datetime.strptime(val, utils.ISO_DATE)
				dt = dt.replace(tzinfo=timezone.utc)
				dtask[key] = dt
		if 'context' in dtask:
			path = dtask['context']
			ctx = root_ctx.add_contexts(path)
		else:
			ctx = root_ctx
		dtask['context'] = ctx
		if 'done' not in dtask or not dtask['done']:
			ctx.population += 1
		id_width = len(hex(dtask['id_'])) - 2 # 0x...
		if id_width > max_width:
			max_width = id_width
		tasks[dtask['id_']] = Task(**dtask)
	for path in data['contexts']:
		ctx = root_ctx.add_contexts(path)
		if 'v' in data['contexts'][path]:
			ctx.visibility = data['contexts'][path]['v']
		if 'p' in data['contexts'][path]:
			ctx.priority = data['contexts'][path]['p']
	meta = {
		'id_width': max_width,
		'last_task': data.get('last_task', None),
		'last_context': data.get('last_context', None)
	}
	return TodoList(root_ctx, tasks, **meta)


def dispatch(args, todolist):
	"""Apply the commands described by the dictionary `args` to the
	`todolist`. Return whether data was modified/updated."""
	change = True
	need_show = any(args[command] for command in SHOW_AFTER)
	show_ctx = None
	last_ctx, last_task = None, None
	if args['add'] or args['task']:
	# Task edition
		if args['add']:
		# Task creation
			task = todolist.add_task(args['<content>'], NOW)
		elif args['task']:
		# Task selection
			task = todolist.get(args['<id>'][0], None)
		if check_none(task, TASK404):
			return False, False
		for mutator in Task.mutators:
			option = '--'+mutator
			if args.get(option) is not None:
				todolist.apply_task_mutator(task.id_, mutator, args[option])
		last_task = task
	elif args['edit']:
		task = todolist.get(args['<id>'][0], None)
		if check_none(task, TASK404):
			return False, False
		new_content = utils.input_from_editor(task.content)
		if new_content.endswith('\n'):
		# hurr durr I'm a text editor I append a newline at the end of files
			new_content = new_content[:-1]
		task.content = new_content
		last_task = task
	elif args['done']:
		last_task = todolist.set_done(args['<id>'])
	elif args['rm']:
		last_task = todolist.remove_tasks(args['<id>'])
	elif args['ctx']:
		changed_something = False
		ctx = todolist.add_contexts(args['<context>'])
		if check_none(ctx, CTX404):
			return False, False
		for mutator in Context.mutators:
			option = '--'+mutator
			if args.get(option) is not None:
				ctx.apply_mutator(mutator, args[option])
				changed_something = True
		if not changed_something:
			todolist.show(args['<context>'])
			change = True
		last_ctx = ctx
	elif args['contexts']:
		path = args['<context>']
		if path is None:
			path = ''
		root = todolist.get_context(path)
		if check_none(root, CTX404):
			return False, False
		root.show_contexts()
	elif args['history']:
		todolist.show_history()
	elif args['purge']:
		todolist.purge()
	else:
		change = False
		need_show = True
		show_ctx = args['<context>']
		if show_ctx is None:
			show_ctx = ''
	if need_show:
		if show_ctx is None:
			show_ctx = todolist.last_context
		ctx = todolist.show(show_ctx)
		if check_none(ctx, CTX404):
			return False, False
		last_ctx = ctx
	if last_task is not None:
		todolist.update_last_task(last_task.id_)
	if last_ctx is not None:
		todolist.update_last_context(last_ctx.path)
	return change


def parse_args(args):
	"""Parse the args dictionary returned by docopt.

	Strings are converted into proper objects. For example, datetime related
	strings are converted into datetime objects, hexadecimal task's
	identifiers are converted to integer and context names are converted into
	context objects.

	If one of the conversion fails, a report is written about the fail. This
	report is None if no failure has been encountered. The report is returned
	by the function"""
	fix_args(args)
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
			if id_ == LAST:
				continue
			try:
				args['<id>'][i] = int(id_, 16)
			except ValueError:
				report = "Invalid task ID: {}".format(id_)
	return report


def fix_args(args):
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
	# command flag to True and the context value to None.
	if any(args[c] for c in COMMANDS):
		return
	if args['<context>'] in COMMANDS:
		args[args['<context>']] = True
		args['<context>'] = None


def main():
	argv = sys.argv[1:]
	if len(argv) == 1 and argv[0] == 'doduh':
		print('Beethoven - Symphony No. 5')
		sys.exit(0)
	args = docopt(__doc__, argv=argv, help=False, version=__version__)

	if args['--help']:
		print(__doc__)
	elif args['--version']:
		print(__version__)
	elif args['--location']:
		print(DATA_LOCATION)
	else:
		report = parse_args(args)
		if report is not None:
			print(report)
			sys.exit(1)

		data = open_data(DATA_LOCATION)
		todolist = import_data(data)
		change = dispatch(args, todolist)
		if change:
			todolist.save(DATA_LOCATION)
		elif todolist.updated_last:
			data['last_task'] = todolist.last_task
			data['last_context'] = todolist.last_context
			save_data(data, DATA_LOCATION)


if __name__ == '__main__':
	main()

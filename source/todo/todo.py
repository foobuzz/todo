#! /usr/bin/env python3

"""todo. CLI todo list manager.

Usage:
  todo [<context>] [--flat|--tidy]
  todo add <title> [--deadline MOMENT] [--start MOMENT] [--context CONTEXT]
    [--priority PRIORITY] [--visibility VISIBILITY]
  todo done <id>...
  todo task <id> [--deadline MOMENT] [--start MOMENT] [--context CONTEXT]
    [--priority PRIORITY] [--visibility VISIBILITY] [--title TITLE]
  todo edit <id>
  todo rm <id>...
  todo ctx <context> [--flat|--tidy] [--priority PRIORITY] [--visibility VISIBILITY] [--name NAME]
  todo mv <ctx1> <ctx2>
  todo rmctx <context> [--force]
  todo contexts [<context>]
  todo history
  todo purge [--force] [--before MOMENT]
  todo --help
  todo --version
  todo --location

Options:
  -d MOMENT, --deadline MOMENT            Set the deadline of a task
  -s MOMENT, --start MOMENT               Set the start-line of a task
  -c CONTEXT, --context CONTEXT           Set the context of a task
  -p INTEGER, --priority INTEGER          Set the priority of a task, or of a
                                          context
  -t TITLE, --title TITLE                 Set the title of a task
  -v VISIBILITY, --visibility VISIBILITY  Set the visibility of a task, or of a
                                          context.
  --name NAME                             Rename a context
  --before MOMENT                         Purge all done task before a moment

"""

import os, sys, sqlite3, functools, configparser
import os.path as op
from datetime import datetime, timezone

from docopt import docopt

from . import utils, data_access
from .rainbow import ColoredStr
from .data_access import DataAccess
from .utils import DATA_DIR


__version__ = '3.0.1'


COMMANDS = {'add', 'done', 'task', 'edit', 'rm', 'ctx', 'contexts', 'history',
	'purge', 'mv', 'rmctx'}

NOW = datetime.utcnow().replace(tzinfo=timezone.utc)

# Icons used to print tasks' properties in the terminal.
# True is the ASCII version for challenged terminals.
# False is the Unicode version.
CONTEXT_ICON = {True: '#', False: '#'}
TIME_ICON = {True: '~', False: '⌛'}
PRIORITY_ICON = {True: '!', False: '★'}

WIDE_HIST_THRESHOLD = 120

TASK_MUTATORS = {
	'deadline': datetime.max,
	'start': None,
	'priority': 1,
	'title': None
}

CONTEXT_MUTATORS = {
	'priority': 1,
	'visibility': 'normal'
}


CONFIG_FILE = op.expanduser(op.join('~', '.toduhrc'))

if os.name == 'posix':
	COLORS = 'on'
else:
	COLORS = 'off'

DEFAULT_CONFIG = configparser.ConfigParser()
DEFAULT_CONFIG['App'] = {
	'layout': 'basic',
	'todo_fashion': 'tidy',
	'show_empty_contexts': True
}
DEFAULT_CONFIG['Colors'] = {
	'colors': COLORS,
	'palette': '8',
	'id': 'yellow',
	'content': 'default',
	'context': 'cyan',
	'deadline': 'cyan',
	'priority': 'green'
}

CONFIG = configparser.ConfigParser(
	allow_no_value=True,
	strict=True
	)
# Loading the config with the default config
CONFIG.read_dict(DEFAULT_CONFIG)
# Loading the user config. Will complete/overwrite the default config
# but will keep default config entries that the user might have removed
CONFIG.read(CONFIG_FILE)

# Editor election: in config file? No -> in OS EDITOR variable? No -> vim
EDITOR = CONFIG.get('App', 'editor', fallback=None)
if EDITOR is None:
	EDITOR = os.environ.get('EDITOR', 'vim')


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
		print(DATA_DIR)
	else:
		report = parse_args(args)
		if len(report) > 0:
			for error in report:
				print(error)
			sys.exit(1)

		daccess = get_data_access()
		result = dispatch(args, daccess)
		if result is not None:
			feedback_code, *data = result
			globals()['feedback_'+feedback_code](*data)
		daccess.exit()


## Argument parsing error messages

INCORRECT_PRIORITY = 'PRIORITY must be an integer.'
INCORRECT_VISIBILITY = "VISIBILITY must be 'normal' or 'hidden'."
INCORRECT_MOMENT = "MOMENT must be in the YYYY-MM-DD format, or the "+\
                   "YYYY-MM-DD HH:MM:SS format, or a delay in the "+\
                   "([0-9]+)([wdhms]) forma."
INCORRECT_CTX_RENAME = "Can't use '.' in context new name "+\
                       "(only right-most context name is updated)."
CANT_RENAME_ROOT = "Can't rename root context."
INVALID_TID = "Invalid task{} ID: {}"


# ARGUMENT PARSERS.
#
# Each function should return a 2-tuple where the first component is a boolean
# indicating whether the value of the argument is correct and has been
# successfully parsed. The second component contains either the parsed value
# (if success) or an error message.

def parse_id(tid_list):
	valid = []
	invalid = []
	for tid in tid_list:
		try:
			valid.append(int(tid, 16))
		except ValueError:
			invalid.append(tid)
	if len(invalid) == 0:
		return True, valid
	else:
		s = 's' if len(invalid) > 1 else ''
		string = ', '.join(invalid)
		error = INVALID_TID.format(s, string)
		return False, error


def parse_priority(p):
	try:
		p_ = int(p)
	except ValueError:
		return False, INCORRECT_PRIORITY
	else:
		return True, p_


def parse_visibility(v):
	if v not in ['normal', 'hidden']:
		return False, INCORRECT_VISIBILITY
	else:
		return True, v


def parse_context(ctx):
	return True, data_access.dbfy_context(ctx)


def parse_moment(moment, direction=1):
	""" Parse a moment, which can be either a string datetime in the allowed
	datetimes format, either a delay (e.g. 2w). In the case of a delay,
	direction indicates in which direction in time the delay is applied to the
	current time. It can either be 1 (future) or -1 (past)."""
	dt = utils.get_datetime(moment, NOW, direction)
	if dt is None:
		return False, INCORRECT_MOMENT
	else:
		return True, dt.strftime(utils.SQLITE_DT_FORMAT)


def parse_deadline(moment):
	""" A deadline-specific wrapper around parse_moment. Case-insensitive
	'none' is accepted and is parsed as 'None' (the string)"""
	# The reason why it returns the string 'None' and not the value None is
	# that docopt gives the value None to all arguments and options that
	# weren't used. Using 'None' (the string) allows us the make the difference
	# between a deadline set as none and no deadline set.
	if moment.lower() == 'none':
		return True, 'None'
	else:
		return parse_moment(moment)


def parse_new_context_name(name):
	if '.' in name:
		return False, INCORRECT_CTX_RENAME
	elif name == '':
		return False, CANT_RENAME_ROOT
	else:
		return True, name


PARSERS = [
	('<id>', parse_id),
	('--priority', parse_priority),
	('--visibility', parse_visibility),
	('--context', parse_context),
	('<context>', parse_context),
	('<ctx1>', parse_context),
	('<ctx2>', parse_context),
	('--deadline', parse_deadline),
	('--start', parse_moment),
	('--before', functools.partial(parse_moment, direction=-1)),
	('--name', parse_new_context_name)
]


def parse_args(args):
	""" Apply application-level parsing of the values of the args dictionary
	*in place*. Returns a report which is a list of errors (strings) that
	might have occured during parsing. There's no waranty that the args
	dictionary will work with the rest of the application if the report
	list isn't empty."""
	fix_args(args)
	report = []
	for arg_name, parser in PARSERS:
		value = args.get(arg_name)
		if value is not None:
			success, result = parser(value)
			if success:
				args[arg_name] = result
			else:
				report.append(result)
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


def get_data_access():
	db_path = data_access.setup_data_access()
	connection = sqlite3.connect(db_path)
	return DataAccess(connection)


# HANDLERS

# Do something with the args dictionary and the data access object then return
# a feedback code as well as some data about how things went. Feedback
# functions (whose names are feedback_<feedback_code>) will then be passed the
# data and should print some feedback based on the data. A handler can also
# return nothing (or None) if no feedback is intended.

def add_task(args, daccess):
	context = args.get('--context')
	options = get_options(args, TASK_MUTATORS, {'--deadline': {'None': None}})
	if context is None:
		context = ''
	id_ = daccess.add_task(args['<title>'], context, options)
	return 'add_task', id_


def update_task(args, daccess):
	tid = args['<id>'][0]
	context = args.get('--context')
	options = get_options(args, TASK_MUTATORS, {'--deadline': {'None': None}})
	upt_count = daccess.update_task(tid, context, options)
	return 'single_task_update', tid, upt_count != 0


def edit_task(args, daccess):
	tid = args['<id>'][0]
	task = daccess.get_task(tid, 'title')
	new_content = utils.input_from_editor(task['title'], EDITOR)
	if new_content.endswith('\n'):
	# hurr durr I'm a text editor I append a newline at the end of files
		new_content = new_content[:-1]
	upt_count = daccess.update_task(tid, options=[('title', new_content)])
	return 'single_task_update', tid, upt_count != 0


def do_task(args, daccess):
	not_found = daccess.set_done_many(args['<id>'])
	return 'multiple_tasks_done', not_found


def remove_task(args, daccess):
	not_found = daccess.remove_many(args['<id>'])
	return 'multiple_tasks_update', not_found


def manage_context(args, daccess):
	path = args['<context>']
	name = args.get('--name')
	options = get_options(args, CONTEXT_MUTATORS)
	exists = True
	if len(options) == 0 and name is None:
		return todo(args, daccess)
	else:
		if name is not None:
			renamed = data_access.rename_context(args['<context>'], name)
			rcount = daccess.rename_context(args['<context>'], name)
			if rcount is None:
				return 'target_name_exists', renamed
			else:
				path = renamed
				exists = rcount != 0
		if len(options) > 0:
			daccess.set_context(path, options)
		elif not exists:
			return 'not_exists_no_options'


def move(args, daccess):
	ctx1 = args['<ctx1>']
	ctx2 = args['<ctx2>']
	source_exists = daccess.context_exists(ctx1)
	if not source_exists:
		return 'ctx_doesnt_exist', ctx1
	else:
		daccess.move_all(ctx1, ctx2)


def remove_context(args, daccess):
	ctx = args['<context>']
	force = args['--force']
	go_ahead = False
	if not force:
		nb_tasks, nb_subctx = daccess.get_basic_context_tally(ctx)
		ans = input('This context contains {} direct undone task(s) and '
			'{} subcontext(s). Continue? y/* '.format(nb_tasks, nb_subctx))
		go_ahead = ans == 'y'
	else:
		go_ahead = True
	if go_ahead:
		removed = daccess.remove_context(ctx)
		if removed == 0:
			return 'ctx_doesnt_exist', ctx


def todo(args, daccess):
	fashion = 'flat' if args['--flat'] else None
	if fashion is None:
		fashion = 'tidy' if args['--tidy'] else None
	if fashion is None:
		fashion = CONFIG.get('App', 'todo_fashion')
	ctx = args.get('<context>', '')
	if ctx is None:
		ctx = ''
	tasks = daccess.todo(ctx, recursive=(fashion == 'flat'))
	if fashion == 'tidy':
		get_empty = CONFIG.getboolean('App', 'show_empty_contexts')
		subcontexts = daccess.get_subcontexts(ctx, get_empty)
	else:
		subcontexts = []
	return 'todo', ctx, tasks, subcontexts


def get_contexts(args, daccess):
	path = args['<context>']
	if path is None:
		path = ''
	contexts = daccess.get_descendants(path)
	return 'contexts', contexts


def get_history(args, daccess):
	tasks = daccess.history()
	gid = daccess.get_greatest_id()
	return 'history', tasks, gid


def purge(args, daccess):
	force = args['--force']
	before = args['--before']
	go_ahead = False
	if force:
		go_ahead = True
	else:
		if before is None:
			q = "This will delete all done tasks. "
		else:
			q = "This will delete all done tasks created before "+\
			"{}. ".format(before)
		q += "This operation is irreversible. Continue? y/* "
		ans = input(q)
		if ans == 'y':
			go_ahead = True
	if go_ahead:
		count = daccess.purge(before)
		return 'purge', count

## DISPATCHING

# Map of the names of the commands to handlers defined above.

DISPATCHER = [
	('add', add_task),
	('task', update_task),
	('edit', edit_task),
	('done', do_task),
	('rm', remove_task),
	('ctx', manage_context),
	('rmctx', remove_context),
	('mv', move),
	('contexts', get_contexts),
	('history', get_history),
	('purge', purge)
]


def dispatch(args, daccess):
	for command, handler in DISPATCHER:
		if args[command]:
			return handler(args, daccess)
	# If no command, fallback to the todo handler
	return todo(args, daccess)


def get_options(args, mutators, converters={}):
	""" Returns a list of 2-tuple in the form (option, value) for all options
	contained in the `mutators` collection if they're also keys of the `args`
	dictionary prefixed by '--' and have a non-None value. If the option (non-
	prefixed) is also a key of the `converters` dictionary then the associated
	value should be another dictionary indicating convertions to be done on
	the value found in `args`.
	e.g.
	args = {'--deadline': 'none'}
	mutators = {'deadline'}
	converters = {'deadline': {'none': None}}
	=> [('deadline', None)]"""
	options = []
	for mutator in mutators:
		cl_opt = '--' + mutator
		if cl_opt in args and args[cl_opt] is not None:
			val = args[cl_opt]
			convertions = converters.get(cl_opt)
			if convertions is not None and val in convertions:
				val = convertions[val]
			options.append((mutator, val))
	return options


## FEEDBACK FUNCTIONS 

TASK_SUBCTX_SEP = '-'*40


def feedback_add_task(id_):
	pass


def feedback_single_task_update(tid, found):
	if not found:
		print('Task {} not found'.format(tid))


def feedback_multiple_tasks_update(not_found):
	if len(not_found) > 0:
		s = 's' if len(not_found) > 1 else ''
		string = ', '.join(utils.to_hex(tid) for tid in not_found)
		print('Task{} not found: {}'.format(s, string))


def feedback_multiple_tasks_done(not_found):
	if len(not_found) > 0:
		string = ', '.join(utils.to_hex(tid) for tid in not_found)
		print('Not found or already done: {}'.format(string))


def feedback_todo(context, tasks, subcontexts):
	layout = CONFIG.get('App', 'layout')
	if len(tasks) != 0:
		id_width = max(len(utils.to_hex(task['id'])) for task in tasks)
	else:
		id_width = 1
	for task in tasks:
		if layout == 'multiline':
			stringyfier = get_multiline_task_string
		else:
			stringyfier = get_basic_task_string
		partial = functools.partial(stringyfier, context, id_width, task)
		safe_print(partial)
	if len(subcontexts) > 0:				
		print(TASK_SUBCTX_SEP)
	for ctx in subcontexts:
		partial = functools.partial(get_context_string, context, id_width, ctx)
		safe_print(partial)


def feedback_target_name_exists(renamed):
	print('Context {} already exists.'.format(
		utils.get_relative_path('', renamed)
		)
	)


def feedback_not_exists_no_options(path, found):
	print("Context does not exist and no option provided. No action done.")


def feedback_contexts(contexts):
	def get_tally(ctx):
		return '{} ({})'.format(ctx['total_tasks'], ctx['own_tasks'])
	struct = [
		('context', lambda a: a, '<', 'path', lambda a: a[1:]),
		('visibility', 10, '<', 'visibility', None),
		('priority', 8, '<', 'priority', None),
		('undone tasks', 12, '<', None, get_tally)
	]	
	utils.print_table(struct, contexts, is_context_default)


def feedback_history(tasks, gid):
	if gid is None:
		print('No history.')
	else:
		struct = get_history_struct(gid)
		utils.print_table(struct, tasks, is_task_default)


def feedback_purge(count):
	s = 's' if count > 1 else ''
	print('{} task{} deleted'.format(count, s))


# String building for todo feedback

# Those functions return a string. They accept a boolean `ascii_` argument
# that indicates whether to build the returned string with ASCII characters
# only (True) or whether non-ASCII characters are allowed (False). Those
# functions will then be partially called with all arguments set except the
# `ascii_` one and the resulting partial will be passed to `safe_print` which
# will take care of trying to print the non-ASCII version and then fallback to
# the ASCII version in case of error from the terminal.

def get_basic_task_string(context, id_width, task, ascii_=False):
	c = get_task_string_components(task, context, ascii_)
	if isinstance(c['id'], ColoredStr):
		ansi_offset = c['id'].lenesc
	else:
		ansi_offset = 0
	left = '{id:>{width}}'.format(width=id_width + ansi_offset + 1, **c)
	right = ['title', 'deadline', 'priority', 'context']
	right = ' '.join(c[a] for a in right if c[a] != '')
	return '{} | {}'.format(left, right)


def get_multiline_task_string(context, id_width, task, ascii_=False):
	c = get_task_string_components(task, context, ascii_)
	return ' {id} / {deadline} {priority} {context}\n {title}\n'.format(**c)


def get_task_string_components(task, ctx, ascii_=False):
	id_str = may_be_colored(
		utils.to_hex(task['id']),
		CONFIG.get('Colors', 'id')
	)

	content_str = may_be_colored(
		task['title'],
		CONFIG.get('Colors', 'content')
	)

	remaining_str = ''
	deadline = get_datetime(task['deadline'])
	if deadline is not None:
		remaining = deadline - NOW
		user_friendly = utils.parse_remaining(remaining)
		remaining_str = '{} {} remaining'.format(TIME_ICON[ascii_], user_friendly)
		remaining_str = may_be_colored(
			remaining_str,
			CONFIG.get('Colors', 'deadline')
		)

	prio_str = ''
	priority = task['priority']
	if not is_task_default(task, 'priority'):
		prio_str = '{}{}'.format(PRIORITY_ICON[ascii_], priority)
		prio_str = may_be_colored(prio_str, CONFIG.get('Colors', 'priority'))

	ctx_path = utils.get_relative_path(ctx, task['ctx_path'])
	if ctx_path == '':
		ctx_str = ''
	else:
		ctx_str = '{}{}'.format(CONTEXT_ICON[ascii_], ctx_path)
		ctx_str = may_be_colored(ctx_str, CONFIG.get('Colors', 'context'))

	return {
		'id': id_str,
		'title': content_str,
		'deadline': remaining_str,
		'priority': prio_str,
		'context': ctx_str
	}


def get_context_string(context, id_width, ctx, ascii_=False):
	hash_str = may_be_colored('#', CONFIG.get('Colors', 'id'))
	if isinstance(hash_str, ColoredStr):
		ansi_offset = hash_str.lenesc
	else:
		ansi_offset = 0
	path = utils.get_relative_path(context, ctx['path'])
	string = '{hash:>{width}} | {path} ({nbr})'.format(
		hash=hash_str,
		width=id_width + ansi_offset + 1,
		path=path,
		nbr=ctx['total_tasks']
	)
	priority = ctx['priority']
	if not is_task_default(ctx, 'priority'):
		prio_str = ' {}{}'.format(PRIORITY_ICON[ascii_], priority)
		string += may_be_colored(prio_str, CONFIG.get('Colors', 'priority'))
	return string


def safe_print(partial):
	try:
		print(partial(ascii_=False))
	except UnicodeEncodeError:
		print(partial(ascii_=True))


def get_datetime(db_dt):
	""" Get a datetime object from the string retrieved from the database."""
	if db_dt is None:
		return None
	return datetime\
		.strptime(db_dt, utils.SQLITE_DT_FORMAT)\
		.replace(tzinfo=timezone.utc)


def is_task_default(task, prop):
	if prop == 'start':
		return task['start'] == task['created']
	return is_default(task, prop, TASK_MUTATORS)


def is_context_default(ctx, prop):
	return is_default(ctx, prop, CONTEXT_MUTATORS)


def is_default(dico, prop, defaults):
	default = defaults.get(prop, None)
	if default is None:
		return False
	else:
		return dico[prop] == default


def get_history_struct(gid):
	gid_len = len(utils.to_hex(gid))
	struct = [
		('id', gid_len + 1, '>', 'id', utils.to_hex),
		('title', lambda a: 3 * (a//4), '<', 'title', None),
		('created', 19, '<', 'created', None),
	]
	if utils.get_terminal_width() > WIDE_HIST_THRESHOLD:
		struct += [
			('start', 19, '<', 'start', None),
			('deadline', 19, '<', 'deadline', None),
			('priority', 8, '>', 'priority', None)
		]
	struct += [
		('context', lambda a: a//4 + a%4, '<', 'ctx_path', lambda a: a[1:]),
		('status', 7, '<', 'done', lambda a: 'DONE' if a is not None else '')
	]
	return struct


def may_be_colored(string, color):
	"""Return a string, colored or not, depending on the CONFIG variable"""
	if CONFIG.getboolean('Colors', 'colors'):
		palette = CONFIG.get('Colors', 'palette')
		return ColoredStr(string, color, palette)
	else:
		return string

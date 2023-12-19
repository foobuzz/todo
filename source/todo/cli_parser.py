import argparse
import functools
import re
import sys
from collections import Counter
from datetime import datetime, timedelta, timezone

from . import data_access, utils
from .utils import NOW, ISO_SHORT


REMAINING = {
	'm': 30.5*24*3600,
	'w': 7*24*3600,
	'd': 24*3600,
	'h': 3600,
}
REMAINING_RE = re.compile('\A([0-9]+)([wdhms])\Z')

ISO_DATE = ISO_SHORT+'T%H:%M:%SZ'
USER_DATE_FORMATS = [
	ISO_SHORT,
	ISO_SHORT+'T%H:%M:%S',
	ISO_SHORT+' %H:%M:%S'
]


COMMANDS = {
	'add', 'done', 'task', 'edit', 'rm', 'ctx', 'contexts', 'history',
	'purge', 'mv', 'rmctx', 'search', 'future', '-h', '--help', '--location',
	'--version', '--install-autocompletion', 'undone', 'ping'}


## Argument parsing error messages

INCORRECT_PRIORITY = 'PRIORITY must be an integer.'
INCORRECT_VISIBILITY = "VISIBILITY must be 'normal' or 'hidden'."
INCORRECT_MOMENT = "MOMENT must be in the YYYY-MM-DD format, or the "+\
                   "YYYY-MM-DD HH:MM:SS format, or a delay in the "+\
                   "([0-9]+)([mwdh]) format."
INCORRECT_PERIOD = "PERIOD must be in the ([0-9]+)([mwdh]) format."
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
	if isinstance(tid_list, str):
		# In the case of the task command, we actually get a lone ID
		tid_list = [tid_list]
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


def parse_context(ctx):
	return True, data_access.dbfy_context(ctx)


def parse_moment(moment, direction=1):
	"""
	Parse a moment, which can be either a string datetime in the allowed
	datetimes format, either a delay (e.g. 2w). In the case of a delay,
	direction indicates in which direction in time the delay is applied to the
	current time. It can either be 1 (future) or -1 (past).
	"""
	dt = _parse_datetime(moment, NOW, direction)
	if dt is None:
		return False, INCORRECT_MOMENT
	else:
		return True, dt.strftime(utils.SQLITE_DT_FORMAT)


def parse_deadline(moment):
	"""
	A deadline-specific wrapper around parse_moment. Case-insensitive
	'none' is accepted and is parsed as 'None' (the string)
	"""
	# The reason why it returns the string 'None' and not the value None is
	# that argparse gives the value None to all arguments and options that
	# weren't used. Using 'None' (the string) allows us the make the difference
	# between a deadline set as none and no deadline set.
	if moment.lower() == 'none':
		return True, 'None'
	else:
		return parse_moment(moment)


def _parse_datetime(string, now, direction=1):
	"""
	Parse the string `string` representating a datetime. The string can be a
	delay such `2w` which means "two weeks". In this case, the datetime is the
	datetime `now` plus/minus the delay. The `direction` option indicates if
	the delay needs to be added to now (+1) or substracted from now (-1). In
	any case, this returns a datetime object.
	"""
	parsing_success, period = parse_period(string)
	if parsing_success:
		offset = direction * timedelta(seconds=period)
		return now + offset
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

	return None


def parse_period(string):
	"""
	Parse the `string` as a period of time, returned in seconds.
	"""
	match = REMAINING_RE.match(string)
	if match is not None:
		value, unit = match.groups()
		return True, int(value) * REMAINING[unit]
	return False, INCORRECT_PERIOD


def parse_new_context_name(name):
	if '.' in name:
		return False, INCORRECT_CTX_RENAME
	elif name == '':
		return False, CANT_RENAME_ROOT
	else:
		return True, name


def parse_dependencies(dependecies):
	if dependecies == ['nothing']:
		return True, []

	for task_id, nb_occ in Counter(dependecies).items():
		if nb_occ > 1:
			return (
				False,
				f"Task {task_id} cannot be specified twice as a dependency."
			)

	return parse_id(dependecies)


def parse_toggle(value):
	return True, {
		'true': 1,
		'false': 0,
		None: None,
	}[value]


PARSERS = [
	('id', parse_id),
	('context', parse_context),
	('ctx1', parse_context),
	('ctx2', parse_context),
	('deadline', parse_deadline),
	('start', parse_moment),
	('period', parse_period),
	('before', functools.partial(parse_moment, direction=-1)),
	('after', functools.partial(parse_moment, direction=-1)),
	('name', parse_new_context_name),
	('depends_on', parse_dependencies),
	('front', parse_toggle),
]


def parse_args(args):
	"""
	Apply application-level parsing of the values of the args dictionary *in
	place*. Returns a report which is a list of errors (strings) that might
	have occured during parsing. There's no waranty that the args dictionary
	will work with the rest of the application if the report list isn't empty.
	"""
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


def parse_cli():
	argv = sys.argv[1:]
	if len(argv) == 0:
		argv = [''] # bare todo with root context
	command, params = argv[0], argv[1:]
	if command in COMMANDS:
		return parse_command(argv)
	else:
		return parse_bare_todo(argv)


def parse_bare_todo(argv):
	parser = argparse.ArgumentParser()
	parser.add_argument('context', nargs='?',
		help="Context to show the tasks of. Defaults to the root context "
		     "(represented by an empty string)"
	)

	style_group = parser.add_mutually_exclusive_group()
	style_group.add_argument('--flat', action='store_true',
		help="Show the tasks of subcontexts as well"
	)
	style_group.add_argument('--tidy', action='store_true',
		help="Only show the tasks of the given context, and list subcontexts"
	)

	args = parser.parse_args(argv)
	return vars(args)


def parse_command(argv):
	parser = argparse.ArgumentParser(
		description="Alternatively, the program might be called this way:\n"
		    "  $ todo [<context>]\n"
		    "to show the tasks of a specific context. If <context> is "
		    "omitted, then the root context is used.",
		formatter_class=argparse.RawTextHelpFormatter
	)
	root_group = parser.add_mutually_exclusive_group()
	root_group.add_argument('--location', action='store_true',
		help="Print the location of the todo data directory"
	)
	root_group.add_argument('--version', action='store_true',
		help="Print the version of the program"
	)
	root_group.add_argument('--install-autocompletion', action='store_true',
		help="Install command-line autocompletion for todo",
	)

	subparsers = parser.add_subparsers()

	add_parser = subparsers.add_parser('add',
		help="Add a new task")
	add_parser.set_defaults(command='add')
	add_parser.add_argument('title',
		help="The title of the task"
	)
	_add_common_task_arguments_to_command_parser(add_parser)
	add_parser.add_argument('-e', '--edit', action='store_true',
		help="Edit the task in a text editor before adding it"
	)

	search_parser = subparsers.add_parser('search',
		help="Search for tasks")
	search_parser.set_defaults(command='search')
	search_parser.add_argument('term',
		help="Substring to be searched in tasks' titles."
	)
	search_parser.add_argument('-c', '--context',
		help="Context to search in, with recursion"
	)
	search_parser.add_argument('--before',
		help="Restrict the search to tasks created before a certain moment. "
		     "Same format than <add --deadline> except that a delay is a "
		     "delay in the past."
	)
	search_parser.add_argument('--after',
		help="Restrict the search to tasks created after a certain moment. "
		     "Same format than <add --deadline>"
	)
	search_parser.add_argument('--case', action='store_true',
		help="Make the search case-sensitive"
	)
	done_group = search_parser.add_mutually_exclusive_group()
	done_group.add_argument('--done', action='store_true',
		help="Restrict the search to done tasks"
	)
	done_group.add_argument('--undone', action='store_true',
		help="Restrict the search to undone tasks"
	)

	done_parser = subparsers.add_parser('done',
		help="Set task(s) as done")
	done_parser.set_defaults(command='done')
	done_parser.add_argument('id', nargs='+',
		help="The list of tasks' IDs to set as done"
	)

	done_parser = subparsers.add_parser('undone',
		help="Cancel the 'done' command on a task")
	done_parser.set_defaults(command='undone')
	done_parser.add_argument('id', nargs='+',
		help="The list of tasks' IDs to set as undone"
	)

	task_parser = subparsers.add_parser('task',
		help="Select a task to apply modifiers to. Options that are shared "
		     "with the add command are documented there")
	task_parser.set_defaults(command='task')
	task_parser.add_argument('id',
		help="ID of the task to apply modifiers to"
	)
	_add_common_task_arguments_to_command_parser(task_parser)
	task_parser.add_argument('-t', '--title',
		help="Rename the task"
	)

	edit_parser = subparsers.add_parser('edit',
		help="Edit the title of a task")
	edit_parser.set_defaults(command='edit')
	edit_parser.add_argument('id',
		help="ID of the task to edit"
	)

	rm_parser = subparsers.add_parser('rm',
		help="Remove task(s) from history")
	rm_parser.set_defaults(command='rm')
	rm_parser.add_argument('id', nargs='+',
		help="The list of tasks' IDs to remove"
	)

	ctx_parser = subparsers.add_parser('ctx',
		help="Select a context to show the tasks of, or to apply modifiers to")
	ctx_parser.set_defaults(command='ctx')
	ctx_parser.add_argument('context',
		help="Context to show or to modify"
	)
	fashion_group = ctx_parser.add_mutually_exclusive_group()
	fashion_group.add_argument('--flat', action='store_true',
		help="Show the tasks of subcontexts as well"
	)
	fashion_group.add_argument('--tidy', action='store_true',
		help="Only show the tasks of the given context, and list subcontexts"
	)
	ctx_parser.add_argument('-p', '--priority', type=int,
		help="The priority of the context, as an integer. The higher the "
		     "integer, the higher the priority. Contexts with a higher "
		     "priority show up first in the list of sub-contexts of a "
		     "context in a todolist"
	)
	ctx_parser.add_argument('-v', '--visibility', choices=['normal', 'hidden'],
		help="Hidden contexts don't show up in the list of sub-contexts of a "
		     "context in a todolist"
	)
	ctx_parser.add_argument('--name',
		help="Name of a context. Cannot contain a dot."
	)

	mv_parser = subparsers.add_parser('mv',
		help="Move all tasks and subcontexts from one context to another")
	mv_parser.set_defaults(command='mv')
	mv_parser.add_argument('ctx1',
		help="Source context"
	)
	mv_parser.add_argument('ctx2',
		help="Destination context"
	)

	rmctx_parser = subparsers.add_parser('rmctx',
		help="Remove a context and all its tasks")
	rmctx_parser.set_defaults(command='rmctx')
	rmctx_parser.add_argument('context',
		help="Context to remove"
	)
	rmctx_parser.add_argument('--force', action='store_true',
		help="Removing a context requires user interaction to confirm the "
		     "action. Setting this option to true skips this step."
	)

	contexts_parser = subparsers.add_parser('context',
		help="List all contexts")
	contexts_parser.set_defaults(command='context')
	contexts_parser.add_argument('context',
		help="Restrict the list to subcontexts of the given context"
	)

	history_parser = subparsers.add_parser('history',
		help="Show tasks history")
	history_parser.set_defaults(command='history')

	purge_parser = subparsers.add_parser('purge',
		help="Remove done tasks from history")
	purge_parser.set_defaults(command='purge')
	purge_parser.add_argument('--force', action='store_true',
		help="Purging requires user interaction to confirm the "
		     "action. Setting this option to true skips this step."
	)
	purge_parser.add_argument('--before',
		help="Only remove done tasks that were created before the given "
		     "moment. Same format than <search --before>"
	)

	future_parser = subparsers.add_parser('future',
		help="Show tasks that will start in the future"
	)
	future_parser.set_defaults(command='future')

	ping_parser = subparsers.add_parser('ping',
		help="Increase the ping counter of a task."
	)
	ping_parser.set_defaults(command='ping')
	ping_parser.add_argument('id', nargs='+',
		help="The list of tasks' IDs to ping",
	)

	return vars(parser.parse_args(argv))


def _add_common_task_arguments_to_command_parser(command_parser):
	command_parser.add_argument('-d', '--deadline',
		help="Deadline of the task, in the YYYY-MM-DD (ISO 8601) format, or "
		     "as a delay in the <n>(s|m|h|d|w) format, where <n> is an "
		     "integer and what follows represents respectively seconds, "
		     "minutes, hours, days or weeks"
	)
	command_parser.add_argument('-s', '--start',
		help="Start line of the task, in the same format than --deadline. "
		     "Defaults to the moment the task is created."
	)
	command_parser.add_argument('--period',
		help="Make the task recurrent by defining a period for it to redisplay "
		     "regularly. Accepts the same duration formats than "
		     "--start and --deadline"
	)
	command_parser.add_argument('-c', '--context',
		help="Context to put the task in. Defaults to the root context"
	)
	command_parser.add_argument('-p', '--priority', type=int,
		help="Priority of the task, as an integer. Higher the interger, "
		     "higher the priority"
	)
	command_parser.add_argument('--depends-on', nargs='+',
		help="Specify which other tasks this task depends on."
	)
	command_parser.add_argument('--front',
		nargs='?', choices=['true', 'false'], const='true',
		help="Show the task in any todo listing that is in an ascendant context "
		     "of the task's context",
	)

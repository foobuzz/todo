import re, os
import os.path as op
from datetime import datetime, timedelta, timezone

from . import rainbow


DATA_DIR_NAME = '.toduh'
DATAFILE_NAME = 'data.json'
DATABASE_NAME = 'data.sqlite'
DATA_CTX_NAME = 'contexts'
VER_FILE_NAME = 'version'

# If a .toduh exists in the current working directory, it's used by the
# program. Otherwise the one in the home is used.
if op.exists(DATA_DIR_NAME) and op.isdir(DATA_DIR_NAME):
	DATA_DIR = DATA_DIR_NAME
else:
	DATA_DIR = op.expanduser(op.join('~', '.toduh'))

DB_PATH = op.join(DATA_DIR, DATABASE_NAME)
VERSION_PATH = op.join(DATA_DIR, VER_FILE_NAME)
DATAFILE_PATH = op.join(DATA_DIR, DATAFILE_NAME)


ISO_SHORT = '%Y-%m-%d'
ISO_DATE = ISO_SHORT+'T%H:%M:%SZ'
USER_DATE_FORMATS = [
	ISO_SHORT,
	ISO_SHORT+'T%H:%M:%S',
	ISO_SHORT+' %H:%M:%S'
]

REMAINING = {
	'w': 7*24*3600,
	'd': 24*3600,
	'h': 3600,
	'm': 60,
	's': 1
}
REMAINING_RE = re.compile('\A([0-9]+)([wdhms])\Z')

SQLITE_DT_FORMAT = '%Y-%m-%d %H:%M:%S'


def print_table(struct, iterable, is_default=lambda obj, p: False):
	""" This function, which is responsible for printing tables to the
	terminal, awaits a "structure", an iterable and a function. The structure
	describes the columns of the table and their properties. It's a list of
	tuples where each tuple describes one column of the table. A tuple has 5
	elements corresponding to the following pieces of information:
	 1. The header of the column, a string
	 2. The width of the column given in number of characters. The width can
	    either be an integer or a function accepting one argument. Widths
	    given as integers will be subtracted from the terminal's width to
	    obtain the "available space". After that, widths given as functions
	    will be evaluated with the available space given as their argument and
	    the functions should return an integer being the actual width of the
	    corresponding column.
	 3. How the name of the column should be aligned in the table header.
	    Value should be either ">", "<", "=" or "^". See Python's format mini-
	    language.
	 4. For mappings, the name of the key of the map to print the value of. If
	    this element is set to None, the object itself will be used for
	    printing.
	 5. A function which takes as argument the value obtained according to the
	    previous element and return the string to finally print.

    The function `is_default` should accept a yielded object and the element 4
    of the tuple and returns True if this objects contains a "default value"
    at the given key. Such values aren't printed in the table.

    See the function get_history_struct to have an example of structure."""
	term_width = get_terminal_width()
	occupied = sum(w if isinstance(w, int) else 0 for _, w, *_ in struct)
	available = term_width - occupied - (len(struct) - 1)
	template, separator = '', ''
	widths = {}
	for header, width, align, *_ in struct:
		w = max(0, width if isinstance(width, int) else width(available))
		widths[header] = w
		template = ' '.join([template, '{{: {}{}}}'.format(align, w)])
		separator = ' '.join([separator, '-'*w])
	template, separator = template[1:], separator[1:] # Starting space

	table = template.format(*(t[0] for t in struct))
	table = '\n'.join([table, separator])
	for obj in iterable:
		values = []
		for h, _, _, a, f in struct:
			f = f if f is not None else lambda a: a
			if is_default(obj, a):
				value = ''
			else:
				if a is None:
					value = obj
				else:
					value = obj[a]
				value = f(value)
			if value is None:
				value = ''
			value = limit_str(str(value), widths[h])
			values.append(value)
		line = template.format(*values)
		table = '\n'.join([table, line])
	print(table)


def limit_str(string, length):
	if len(string) <= length:
		return string
	else:
		if length <= 3:
			return string[:length]
		else:
			return string[:length-3] + '...'


def get_datetime(string, now, direction=1):
	"""Parse the string `string` representating a datetime. The string can be
	a delay such `2w` which means "two weeks". In this case, the datetime is
	the datetime `now` plus/minus the delay. The `direction` option indicates
	if the delay needs to be added to now (+1) or substracted from now (-1).
	In any case, this returns a datetime object."""
	match = REMAINING_RE.match(string)
	if match is not None:
		value, unit = match.groups()
		seconds = int(value) * REMAINING[unit]
		offset = direction * timedelta(seconds=seconds)
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


def parse_remaining(delta):
	null_delta = timedelta(0)
	sign = '' if delta >= null_delta else '-'
	delta = abs(delta)
	seconds = 3600 * 24 * delta.days + delta.seconds
	if seconds >= 2 * 24 * 3600:
		string = '{} days'.format(delta.days)
	elif seconds >= 2*3600:
		string = '{} hours'.format(24*delta.days + delta.seconds // 3600)
	elif seconds >= 2*60:
		string = '{} minutes'.format(seconds // 60)
	else:
		string = '{} seconds'.format(seconds)
	return '{}{}'.format(sign, string)


def input_from_editor(init_content, editor):
	import subprocess
	with CustomTemporaryFile() as filename:
		with open(filename, 'w') as edit_file:
			edit_file.write(init_content)
		subprocess.call([editor, filename])
		with open(filename) as edit_file:
			new_content = edit_file.read()
	return new_content


class CustomTemporaryFile:

	def __enter__(self):
		import uuid
		self.path = op.join(DATA_DIR, '.todoedit-'+uuid.uuid4().hex)
		return self.path

	def __exit__(self, type_, value, traceback):
		os.remove(self.path)
		return type_ is None


def get_relative_path(parent, desc):
	rel = desc[len(parent):]
	if rel.startswith('.'):
		rel = rel[1:]
	return rel


def to_hex(integer):
	return hex(integer)[2:] # 0x...


def get_terminal_width():
	fallback = 80
	import subprocess
	process = subprocess.Popen('stty size', shell=True,
		universal_newlines=True,
		stdout=subprocess.PIPE,
		stderr=subprocess.PIPE
	)
	stdout, stderr = process.communicate()
	status = process.returncode
	if status != 0 or stderr != '':
		return fallback
	result = stdout.split()
	if len(result) != 2:
		return fallback
	cols = result[1]
	try:
		cols = int(cols)
	except ValueError:
		return fallback
	return cols


def sqlite_date_to_local(sqlite_date):
	if sqlite_date is None:
		return ''
	dt = datetime.strptime(sqlite_date, SQLITE_DT_FORMAT)
	dt = dt.replace(tzinfo=timezone.utc)
	try:
		local_dt = dt.astimezone(tz=None)
	except ValueError:
		# Some exotic dates such as '0001-01-01 00:00:00' don't work well
		return sqlite_date
	return local_dt.strftime(SQLITE_DT_FORMAT)


def get_highlights_term(string, term, str_color, case=False):
	if str_color is not None:
		escape = rainbow.get_escape(*str_color)
		if escape is None:
			str_color = None

	if len(term) > 0:
		def term_repl(matchobj):
			repl = '\33[1;31m' + matchobj.group(0) + '\33[0m'
			if str_color is not None:
				repl = '\33[0m' + repl + escape
			return repl
		args = dict(
			pattern=term,
			repl=term_repl,
			string=string
		)
		if not case:
			args.update(flags=re.IGNORECASE)
		highlighted = re.sub(**args)
		if str_color:
			highlighted = escape + highlighted + '\33[0m'
		return highlighted
	else:
		if str_color is not None:
			return escape + string + '\33[0m'
		else:
			return string


def compare_versions(vA, vB):
	# ((major, minor, patch), tag, tagNumber)
	(releaseA, tagA, tagnumA), (releaseB, tagB, tagnumB) = [
		parse_version(v) for v in [vA, vB]
	]
	if releaseA != releaseB:
		return 1 if releaseA > releaseB else -1
	else:
		if tagA is None:
			if tagB is None:
				return 0
			elif tagB < 'final':
				return 1
			else:
				return -1
		elif tagB is None:
			if tagA < 'final':
				return -1
			else:
				return 1
		elif tagA != tagB:
			return 1 if tagA > tagB else -1
		else:
			if tagnumA > tagnumB:
				return 1
			elif tagnumA == tagnumB:
				return 0
			else:
				return -1


def parse_version(v):
	"""
	A version is in the form <major>.<minor>.<patch><tag><tagnumber>
	<minor> and <patch> can be omitted (in which case they count for 0)
	<tag> and <tagnumber> are optional
	"""
	undotted = v.split('.')
	if len(undotted) == 0:
		raise ValueError("Versio number cannot be empty")
	if len(undotted) > 3:
		raise ValueError("Version number cannot have more than 3 dots")
	tag_match = re.match('([0-9]+)([a-z]+)([0-9]+)?', undotted[-1])
	if tag_match is not None:
		least_number, tag, tagnumber = tag_match.groups()
	else:
		least_number, tag, tagnumber = undotted[-1], None, None
	if tagnumber is None:
		tagnumber = 0
	release = tuple(undotted[:-1]) + (least_number,)
	while len(release) < 3:
		release = release + (0,)
	release = tuple(int(n) for n in release)
	return (release, tag, int(tagnumber))

import os, re
from datetime import datetime, timedelta, timezone

from .config import CONFIG


ISO_SHORT = '%Y-%m-%d'
ISO_DATE = ISO_SHORT+'T%H:%M:%SZ'
USER_DATE_FORMATS = [
	ISO_SHORT,
	ISO_SHORT+'T%H:%M:%S',
]

REMAINING = {
	'w': 7*24*3600,
	'd': 24*3600,
	'h': 3600,
	'm': 60,
	's': 1
}
REMAINING_RE = re.compile('\A([0-9]+)([wdhms])\Z')

# Editor election: in config file? No -> in OS EDITOR variable? No -> vim
EDITOR = CONFIG.get('App', 'editor', fallback=None)
if EDITOR is None:
	EDITOR = os.environ.get('EDITOR', 'vim')


def get_history_struct(id_width, wide):
	struct = [
		('id', id_width, '>', 'id_', lambda a: hex(a)[2:]),
		('content', lambda a: 3 * (a//4), '<', 'content', lambda a: a),
		('created', 10, '<', 'created', lambda a: a.strftime(ISO_SHORT)),
	]
	if wide:
		struct += [
			('start', 10, '<', 'start', lambda a: a.strftime(ISO_SHORT)),
			('deadline', 10, '<', 'deadline', lambda a: a.strftime(ISO_SHORT)),
			('priority', 8, '>', 'priority', lambda a: str(a)),
			('visibility', 10, '<', None, lambda a: a.get_visibility())
		]
	struct += [
		('context', lambda a: a//4 + a%4, '<', 'context', lambda a: a.name),
		('status', 7, '<', 'done', lambda a: 'DONE' if a else '')
	]
	return struct


def print_table(struct, iterable, term_width):
	"""This function, which is responsible for printing tables to the
	terminal, awaits a "structure", an iterable and the width of the display.
	The structure describes the columns of the table and their properties.
	It's a list of tuples where each tuple describes one column of the table.
	A tuple has 5 elements corresponding to the following pieces of
	information:
	 1. The header of the column, a string
	 2. The width of the column given in number of characters. The width can
        either be an integer or a function accepting one argument. Widths
        given as integers will be subtracted from the display's width to
        obtain the "available space". After that, widths given as functions
        will be evaluated with the available space given as their argument and
        the functions should return an integer being the actual width of the
        corresponding column.
	 3. How the name of the column should be aligned in the table header.
        Value should be either ">", "<", "=" or "^". See Python's format mini-
        language.
	 4. The name of the attribute of the objects yielded by the iterable to
        print in the table. This attribute's value will be accessed using
        hasattr. If this element of the tuple is set to None, the object
        itself will be used for printing.
	 5. A function which takes as argument the value obtained according to the
        previous element and return the string to finally print.

    See the function get_history_struct to have an example of structure."""
	occupied = sum(w if isinstance(w, int) else 0 for _, w, *_ in struct)
	available = term_width - occupied - (len(struct) - 1)
	template, separator = '', ''
	widths = {}
	for header, width, align, *_ in struct:
		w = width if isinstance(width, int) else width(available)
		widths[header] = w
		template = ' '.join([template, '{{: {}{}}}'.format(align, w)])
		separator = ' '.join([separator, '-'*w])
	template, separator = template[1:], separator[1:] # Starting space

	table = template.format(*(t[0] for t in struct))
	table = '\n'.join([table, separator])
	for obj in iterable:
		values = []
		for h, _, _, a, f in struct:
			if a is None:
				value = f(obj)
			elif hasattr(obj, 'is_default') and obj.is_default(a):
				value = ''
			else:
				value = f(getattr(obj, a))
			value = limit_str(value, widths[h])
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


def get_datetime(string, now):
	"""Parse the string `string` representating a datetime. The string can be
	a delay such `2w` which means "in two weeks". In this case, the datetime
	is the datetime `now` plus the delay. In any case, this returns a datetime
	object."""
	match = REMAINING_RE.match(string)
	if match is not None:
		value, unit = match.groups()
		seconds = int(value) * REMAINING[unit]
		return now + timedelta(seconds=seconds)
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


def input_from_editor(init_content):
	import tempfile, subprocess # Tempfile being slow to import
	with tempfile.NamedTemporaryFile(mode='w+') as edit_file:
		edit_file.write(init_content)
		edit_file.flush()
		subprocess.call([EDITOR, edit_file.name])
		edit_file.seek(0)
		new_content = edit_file.read()
	return new_content


def parse_list(string):
	""" "foo, bar" => ["foo", "bar"]"""
	ls = [e.strip() for e in string.split(',')]
	return [] if ls[0] == '' else ls

import textwrap, re


DEFAULT_WIDTH = 80


def wrap_text(text, width=DEFAULT_WIDTH, smart=False):
	wrapped_text = ""
	lines = text.splitlines()
	for i, line in enumerate(lines):
		if smart:
			go_wrap, sub_indent = smart_line(line)
		else:
			go_wrap, sub_indent = True, ''
		if go_wrap:
			prod_line = '\n'.join(textwrap.wrap(
				line,
				width=width,
				subsequent_indent=sub_indent
			))
		else:
			prod_line = line
		wrapped_text += prod_line
		if i < len(lines) - 1:
			wrapped_text += '\n'
	return wrapped_text


SPECIAL_LINES = [
	(re.compile('( {,3}> ?).*'),                   1), # Quote
	(re.compile('(#+ ?).*'),                       1), # Settext heading
	(re.compile('( {,3}([+\-*]|[0-9][.\)]) ?).*'), 1), # List item
]


def smart_line(line):
	if line.startswith(' '*4) or line.startswith('\t'): # Code block
		return False, ''
	for regex, gr in SPECIAL_LINES:
		match_obj = re.match(regex, line)
		if match_obj is not None:
			return True, ' '*len(match_obj.group(gr))
	return True, ''

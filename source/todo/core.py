from . import utils, text_wrap


def editor_edit_task(title, content, editor):
	"""
	Opens the text editor `editor` to edit a task's `title` and `content`.
	Returns the updated title and content after editing is done.
	"""
	init_content = get_task_full_content(title, content)
	full_content = utils.input_from_editor(init_content, editor)
	title, content = parse_task_full_content(full_content)
	return title, content


def get_task_full_content(title, content, wrap_width=None, smart_wrap=False):
	"""
	Return the full text of a task from its `title` and `content`. If
	`wrap_width` is not None, then both the title and content are word-wrapped
	to be contained in the given width. If `smart_wrap` is True, then the
	word-wrapping cleverly handles things such as list, quotes, etc.
	"""
	if wrap_width is not None:
		title = text_wrap.wrap_text(title, wrap_width, smart_wrap)
		if content is not None:
			content = text_wrap.wrap_text(content, wrap_width, smart_wrap)
	title_width = max(len(line) for line in title.splitlines())
	if content is None:
		return title
	else:
		return '{}\n{}\n{}'.format(title, '='*title_width, content)


def parse_task_full_content(full_content):
	"""
	Return a tuple (title, content) extracted from the content found in a file
	edited through `todo edit` or `todo add [<title>] --edit`
	"""
	title, content = '', None
	state = 'title'
	lines = full_content.splitlines(keepends=True)
	for i, line in enumerate(lines):
		if state == 'title' and line.startswith('==='):
			state = 'content'
			continue
		if state == 'title':
			title += line
		elif state == 'content':
			if content is None:
				content = ''
			content += line

	# Removes blank characters at the right of the title (newline leading to
	# settext heading underlining and potential newline added by text editors)
	title = title.rstrip()

	return title, content

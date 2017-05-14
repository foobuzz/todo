from . import utils


def editor_edit_task(title, content, editor):
	"""
	Opens the text editor `editor` to edit a task's `title` and `content`.
	Returns the updated title and content after editing is done.
	"""
	init_content = get_task_init_content(title, content)
	full_content = utils.input_from_editor(init_content, editor)
	title, content = parse_task_full_content(full_content)
	return title, content


def get_task_init_content(title, content):
	"""
	Return the initial content to load a text editor with when `todo add
	[<title>] --edit` or `todo edit` is called.
	"""
	if content is None:
		return '{}\n{}'.format(title, '='*len(title))
	else:
		return '{}\n{}\n{}'.format(title, '='*len(title), content)


def parse_task_full_content(full_content):
	"""
	Return a tuple (title, content) extracted from the content found in a file
	edited through `todo edit` or `todo add [<title>] --edit`
	"""
	title, content = '', ''
	state = 'title'
	lines = full_content.splitlines(keepends=True)
	for i, line in enumerate(lines):
		if state == 'title' and line.startswith('==='):
			state = 'content'
			continue
		if state == 'title':
			title += line
		elif state == 'content':
			content += line

	# Removes blank characters at the right of the title (newline leading to
	# settext heading underlining and potential newline added by text editors)
	title = title.rstrip()

	return title, content

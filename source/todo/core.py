from datetime import datetime, timedelta

from . import text_wrap
from . import utils
from .types import DoTaskReportType


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
	state = 'number_title' if full_content.startswith('# ') else 'title'
	lines = full_content.splitlines(keepends=True)
	for i, line in enumerate(lines):
		if state == 'title' and line.startswith('==='):
			state = 'content'
			continue
		if state == 'number_title' and line.startswith('\n'):
			state = 'content'
		if state in ['title', 'number_title']:
			title += line
		if state == 'content':
			if content is None:
				content = ''
			content += line

	# Removes blank characters at the right of the title (newline leading to
	# settext heading underlining and potential newline added by text editors)
	title = title.rstrip()

	if title.startswith('# '):
		title = title[2:]

	return title, content


def do_recurring_task(task, daccess):
	last_occurrence, next_occurrence = get_neighbourhood_occurrences(
		datetime.strptime(task['start'], utils.SQLITE_DT_FORMAT),
		task['period'],
	)

	report = {
		'task_id': task['id'],
		'next_occurrence_datetime': next_occurrence,
	}

	last_done = daccess.get_last_occurrence_done(task['id'])

	if last_done > last_occurrence:
		report['report_type'] = DoTaskReportType.occurrence_ALREADY_DONE
		return report

	daccess.add_done_occurrence(task['id'])
	report['report_type'] = DoTaskReportType.OK

	return report


def get_neighbourhood_occurrences(start: datetime, period: int):
	"""
	From a start datetime and a period (in seconds), return the last and next
	occurrence of the period around the current datetime.
	"""
	next_occurrence = start
	now = datetime.utcnow()
	while next_occurrence <= now:
		next_occurrence += timedelta(seconds=period)
	return next_occurrence - timedelta(seconds=period), next_occurrence

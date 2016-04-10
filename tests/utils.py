import subprocess, re
import os.path as op
from importlib import machinery


COMMAND_W_DT = '{NOW\+(.*)}'


def parse_trace(trace_file, get_datetime):
	sequence = []
	command, out = None, None
	for line in trace_file:
		if line.startswith('$ '):
			if command is not None:
				sequence.append((command, out))
			command = line[2:-1]
			match = re.search(COMMAND_W_DT, command)
			if match is not None:
				delay = match.group(1)
				dt = get_datetime(delay)
				dt_string = dt.strftime('%Y-%m-%d')
				command = re.sub(COMMAND_W_DT, dt_string, command)
			out = ''
		else:
			out += line
	sequence.append((command, out))
	return sequence


def test_trace(filename, get_datetime, print_commands=False):
	with open(filename) as trace_file:
		sequence = parse_trace(trace_file, get_datetime)
	for command, out in sequence:
		if print_commands:
			print(command)
		process = subprocess.Popen(command, shell=True,
			universal_newlines=True,
			stdout=subprocess.PIPE,
			stderr=subprocess.PIPE)
		stdout, stderr = process.communicate()
		status = process.returncode
		assert status == 0
		assert stderr == ''
		assert out == stdout

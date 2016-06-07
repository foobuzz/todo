import configparser, os, platform
import os.path as op


DATA_DIR = op.expanduser(op.join('~', '.toduh'))
DATA_LOCATION = op.join(DATA_DIR, 'data.json')
DATA_FILE_NAME = op.abspath(op.join(os.getcwd(), '.todo_datafile'))

# We check for a .todo_datafile in the current working directory that is to be
# used in place of the default ~/.toduh/data.json
if op.exists(DATA_FILE_NAME):
	DATA_LOCATION = DATA_FILE_NAME

CONFIG_FILE = op.expanduser(op.join('~', '.toduhrc'))

if platform.system() == 'Windows':
	COLORS = 'on'
else:
	COLORS = 'off'

DEFAULT_CONFIG = configparser.ConfigParser()
DEFAULT_CONFIG['App'] = {
	'show_after': 'edit'
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

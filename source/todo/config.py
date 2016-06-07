import configparser, os
import os.path as op


DATA_DIR_NAME = '.toduh'
DATA_FILE_NAME = 'data.json'
DATA_CTX_NAME = 'contexts'

# If a .toduh exists in the current working directory, it's used by the
# program. Otherwise the one in the home is used.
if op.exists(DATA_DIR_NAME) and op.isdir(DATA_DIR_NAME):
	DATA_DIR = DATA_DIR_NAME
else:
	DATA_DIR = op.expanduser(op.join('~', '.toduh'))
DATA_LOCATION = op.join(DATA_DIR, DATA_FILE_NAME)
DATA_CTX = op.join(DATA_DIR, DATA_CTX_NAME)

CONFIG_FILE = op.expanduser(op.join('~', '.toduhrc'))

if os.name == 'posix':
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

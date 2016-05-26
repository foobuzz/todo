import configparser, os
import os.path as op


DATA_DIR = op.expanduser(op.join('~', '.toduh'))
DATA_LOCATION = op.join(DATA_DIR, 'data.json')
DATA_FILE_NAME = op.abspath(op.join(os.getcwd(), '.todo_datafile'))

# We check for a .todo_datafile in the current working directory that is to be
# used in place of the default ~/.toduh/data.json
if op.exists(DATA_FILE_NAME):
	DATA_LOCATION = DATA_FILE_NAME

CONFIG_FILE = op.expanduser(op.join('~', '.toduhrc'))
DEFAULT_CONFIG_FILE = op.join(DATA_DIR, '.defaultrc')

DEFAULT_CONFIG = configparser.ConfigParser()
DEFAULT_CONFIG.read(DEFAULT_CONFIG_FILE)

CONFIG = configparser.ConfigParser(
	allow_no_value=True,
	strict=True
	)
# Loading the config with the default config
CONFIG.read_dict(DEFAULT_CONFIG)
# Loading the user config. Will complete/overwrite the default config
# but will keep default config entries that the user might have removed
CONFIG.read(CONFIG_FILE)


def parse_list(string):
	ls = [e.strip() for e in string.split(',')]
	return [] if ls[0] == '' else ls

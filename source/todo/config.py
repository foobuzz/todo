import configparser
import os.path as op


DATA_DIR = op.expanduser('~/.toduh')

# We check for the .dev file whose existence indicates that
# the datafile to use is ~/.doduh/data2.json instead of
# ~/.toduh/data.json
project_path = op.dirname(__file__)
dev_flag = op.join(project_path, '.dev')
if op.exists(dev_flag) and op.isfile(dev_flag):
	DATA_FILENAME = 'data2.json'
else:
	DATA_FILENAME = 'data.json'
DATA_LOCATION = op.join(DATA_DIR, DATA_FILENAME)

CONFIG_FILE = op.expanduser(op.join('~', '.toduhrc'))
DEFAULT_CONFIG_FILE = op.join(DATA_DIR, '.defaultrc')

DEFAULT_CONFIG = configparser.ConfigParser()
DEFAULT_CONFIG.read(DEFAULT_CONFIG_FILE)

# WHY AM I SHOUTING?

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

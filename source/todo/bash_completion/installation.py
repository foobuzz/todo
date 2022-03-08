from pathlib import Path


FILENAME_CANDIDATES = ['.zshrc', '.bashrc']
FILEPATH_CANDIDATES = [Path.home() / Path(fn) for fn in FILENAME_CANDIDATES]

TODO_AUTOCOMPLETION_MARK = (
	"# todocli autocompletion (this was added by: todo --install-autocompletion)"
)


def install_autocompletion():
	config_filepath = None
	for filepath in FILEPATH_CANDIDATES:
		if filepath.exists():
			config_filepath = filepath
			break

	if config_filepath is None:
		print(
			"No appropriate config file was found. todo looks for the "
			"following files: "
			"{}".format(', '.join(str(p) for p in FILEPATH_CANDIDATES))
		)
		return

	already_there = False
	with open(str(config_filepath)) as config_file:
		for line in config_file:
			if line.strip() == TODO_AUTOCOMPLETION_MARK:
				already_there = True
				break

	if already_there:
		print(
			"Autocompletion is already installed in config file "
			"{}".format(str(config_filepath))
		)
		return

	autocompletion_payload = get_autocompletion_payload()

	with open(str(config_filepath), 'a') as config_file:
		config_file.write('\n\n')
		config_file.write(TODO_AUTOCOMPLETION_MARK + '\n')
		config_file.write(autocompletion_payload)

	print(
		"Autocompletion installed in config file {}\n"
		"You may `source {}` to enjoy it on this terminal.".format(
			config_filepath, config_filepath,
		)
	)


def get_autocompletion_payload():
	import pkg_resources

	filename = pkg_resources.resource_filename('todo.bash_completion', 'toduh.sh')
	with open(filename) as f:
		payload = f.read()
	return payload

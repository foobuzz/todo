import textwrap, re


TEXT = """todo
====

A simple command line todo list manager which can be as powerful as you want it do be.

	$ todo add "Fix the stuff"
	$ todo
	    1 | Fix the stuff
	$ todo add "Fix the other thing"
	$ todo
	    1 | Fix the stuff
	    2 | Fix the other thing
	$ todo done 1
	$ todo
	    2 | Fix the other thing


## Installation

	pip3 install todocli

`sudo` would be needed for:

 * a system-wide installation (that is, without the `--user` flag)
 * the installation of auto-completion for the `todo` command Lorem ipsum dolor sit amet, consectetur adipiscing elit. Curabitur eleifend, nisi eu tempor ultrices, erat augue euismod purus, nec condimentum nunc nulla eu nunc. Nulla convallis, massa mollis efficitur commodo, lectus neque tincidunt orci, id vulputate leo odio ut massa. Cras a libero vel tortor consectetur mollis. Etiam sem urna, vulputate sed venenatis id, dapibus porta nibh. Sed condimentum fermentum leo, ut mattis urna scelerisque in. Praesent mollis mi dui, sit amet pellentesque eros imperdiet hendrerit. Donec ac vestibulum metus. Pellentesque habitant morbi tristique senectus et netus et malesuada fames ac turpis egestas. Donec a neque eget metus tincidunt elementum. Aliquam lacinia consequat tellus, et aliquet felis suscipit nec. Maecenas nisl mauris, rhoncus vitae ex et, volutpat varius justo. Proin auctor vulputate est eget blandit. Quisque dignissim et sapien nec suscipit. Nam ultrices semper pharetra. Maecenas vel metus at nisl pharetra suscipit ac non lacus. Duis rutrum eros dui, vitae facilisis massa mollis quis. 

Some citation:

 > Lorem ipsum dolor sit amet, consectetur adipiscing elit. Curabitur eleifend, nisi eu tempor ultrices, erat augue euismod purus, nec condimentum nunc nulla eu nunc. Nulla convallis, massa mollis efficitur commodo, lectus neque tincidunt orci, id vulputate leo odio ut massa. Cras a libero vel tortor consectetur mollis. Etiam sem urna, vulputate sed venenatis id, dapibus porta nibh. Sed condimentum fermentum leo, ut mattis urna scelerisque in. Praesent mollis mi dui, sit amet pellentesque eros imperdiet hendrerit. Donec ac vestibulum metus. Pellentesque habitant morbi tristique senectus et netus et malesuada fames ac turpis egestas. Donec a neque eget metus tincidunt elementum. Aliquam lacinia consequat tellus, et aliquet felis suscipit nec. Maecenas nisl mauris, rhoncus vitae ex et, volutpat varius justo. Proin auctor vulputate est eget blandit. Quisque dignissim et sapien nec suscipit. Nam ultrices semper pharetra. Maecenas vel metus at nisl pharetra suscipit ac non lacus. Duis rutrum eros dui, vitae facilisis massa mollis quis. 


## Documentation

 * [User guide](https://github.com/foobuzz/todo/blob/master/doc/guide.md)
 * [Reference](https://github.com/foobuzz/todo/blob/master/doc/reference.md)


## Development

### Running a development version

To run the program in development, clone the project (or download its zip) and go to the `source` directory. You can run the source by executing:

	./todo.py

You can create a directory named `.toduh` in the `source` directory which will carry development-specific data as long as you run `./todo.py` from the `source` directory.

### Tests

To run the tests, go the `source` directory and execute:

	./test.py

By default, this only launches the unit tests. There are also functional tests. The fonctional tests uses the files in `tests/traces`. These files contain a list of commands (lines introduced by `$`), each above the standard output they should produce. The functional tests run each of the commands in a subprocess and compare their output to the expected output. The test is ran on a new datafile each time, which doesn't affect the regular datafile.

To run the functional tests, use the `-f` option. The `-a` option runs both unit and functional tests. The `-v` option, when used with the functional test, prints the commands being executed.


### Contributing

Submit issues for bug reports or enhancement ideas.


### License

MIT. See [LICENSE.txt](https://github.com/foobuzz/todo/blob/master/LICENSE.txt)
"""

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


if __name__ == '__main__':
	print(wrap_text(TEXT, smart=True))

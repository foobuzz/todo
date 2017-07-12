todo
====

A simple command-line todolist manager which can be as powerful as you want it to be.

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
 * the installation of auto-completion for the `todo` command


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
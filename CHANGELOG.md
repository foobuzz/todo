## 3.2.1

Fix https://github.com/foobuzz/todo/pull/15 by https://github.com/xu4wang.

## 3.2

### Features

 * New command: `todo task <id>` shows the detail of a task
 * Full-text editing of task with title interpreted as a settext heading
 * Title word-wrapping

### Details

 * Various bugfixes
 * Argument parsing is handled by standard argparse for better performance

## 3.1.3

Fix https://github.com/foobuzz/todo/issues/10 and https://github.com/foobuzz/todo/issues/12

## 3.1.2

Bugfix at intialization: todo was trying to create its version file into its directory (`~/.toduh`) without the directory having been created in a first place.

## 3.1.1

The YYYY-MM-DD HH:MM:SS format for MOMENT arguments wasn't working, contrarily to what was specified in the documentation. The format that was supported was actually YYYY-MM-DDTHH:MM:SS. This hotfix introduces support for the YYYY-MM-DD HH:MM:SS format. It also keeps support for the YYYY-MM-DDTHH:MM:SS format and adds it to the documentation.


## 3.1

### Features

 * Search feature
 * Datetimes in the `history` output are converted to local time
 * Negatime timedeltas (e.g. deadline in the past) are parsed too

### Details

 * System for adding stuff to the database (tables, indexes, etc) depending on what version is already installed


## 3.0.1

Management of the temporary file created for editing purposes with the `edit` command is handled with a custom context manager instead of Python's `NamedTemporaryFile` as the documentation states that depending on platform external programs might not be able to write to such file.


## 3.0

### Breaking

 * Contexts are now listed belows the list of tasks, along with the number of tasks they contain. The previous behaviour (tasks of subcontexts being mixed with general tasks) can be achieved with the `--flat` option.
 * The `purge` command now awaits user input to validate the purge, unless the `--force` flag is used. It also supports a new option `--before` which awaits a date or delay. The value indicates before which date done tasks will be deleted. Tasks created after the given date will be kept.
 * The concept of visibility for tasks has been abandonned
 * The `LAST` selector if not supported anymore, as well as the ability to re-show the todolist after a certain command.

### Features

 * Three new context-management commands or options:
 	* `mv <ctx1> <ctx2>` to move everything from one context to another
 	* `rm <ctx>` to remove a context (and all of its descendance)
 	* The `--name` option for the `ctx` command which serves as renaming a context
 * Cancelling a deadline with `--deadline none`
 * Support for an alternative layout where tasks are printed on two lines, one for metadata and one for the title of the task. The configuration file now accepts a `layout` key with value which can be either `basic` (default) or `multiline`.

### Details

The persistance is now handled by sqlite3 instead of a JSON datafile. Performance if similar on small todolists but will obvously increase for huge task bases. Most of the codebase had to be rewritten to handle such change, for the greater good!


## 2.1

### Features

 * Multiples task IDs can be used with the commands `done` and `rm` to respectively set done and remove multiple tasks at once. Example: `todo done 11 1f 2a`
 * The text describing a task can be modified either using the `-t/--text` option followed by the new text, or by using the new `edit` command which opens a text editor loaded with the task's content. In such case, the task's content is updated upon closing the editor (assuming the changes has been saved). Examples: `todo task 42 --text "This is a new text for task 42"` or `todo edit 42` to use the text editor
 * The todolist is now printed with colors for IDs, contexts, priorities and deadlines (only on Linux)
 * The application can be customized using a configuration file which is searched at `~/.toduhrc`. This file is in the INI format and can be edited to specify what editor to use with the `edit` command and to customize the colors used for printing the todolist (or disabling colors altogether).
 * It's possible to use independant todolists for specific directories by creating a folder `.toduh` inside such directory. If such a folder is found in the current working directory, then it'll be used to store the data of the todolist specific to this directory. Otherwise, `~/.toduh` is used.
 * When printing the todolist for a specific context, contexts of tasks are printed relatively to the given context. For example, if the tasks 42 has a context `watchlist.movies` and the command is `todo watchlist` then the task 42 will show a context of `movies`, in contrary to the whole `watchlist.movies` in the previous versions.
 * It's possible to show all the subcontexts of a specific context by giving the context's name to the `context` command
 * The `LAST` identifier for tasks (resp. contexts) keeps a reference to the last used tasks (resp. context)
 * It's possible to configure the application so that the todolist is printed again after a command such as `done`. In this case, the LAST context is used to print the todolist
 * Auto-completion in the terminal is supported for commands, contexts and values of visibility (only on Linux)

### Details

 * The TodoList class now supports the mapping protocol and internally uses an OrderedDict to store the tasks (with tasks' ID as keys)
 * The Context object is now a tree. The TodoList has a reference to the root of the main context tree.


## 2

### Breaking

New template for command-line interface: `todo <command> <value> [<options>]`. The features of v1 are usable thanks to the following commands:

 * `add <content> [<options>]` to add a task
 * `done <task_id>` to mark a task as done using its ID
 * `show [<context>]` to show the tasks of a given context. If no context is given then the behavior is the same as a bare `todo`
 * `task <task_id> <options>` to apply option(s) to an existing task using its ID
 * `ctx <context> [<options>]` to apply option(s) to a context using its name.

### Features

 * `contexts`: lists all contexts ever used in the history of tasks, each one being displayed with its properties and the number of tasks this context currently has (including tasks belonging to subcontexts of this context)
 * `history`: shows full task history, including task that have been done
 * `rm <task_id>`: removes a task from history thanks to its ID.
 * `purge`: removes all task marked as done

### Details

 * Usage of the `docopt` module to parse argument instead of Python built-in argparse
 * Exportation of some utility function to an `utils.py` module and restructuration of the project under a Python package
 * Contexts have now their own class, which heritates with Task from a HasDefaults super class
 * Command-line arguments are parsed and transformed into objects. If a value type is unexpected, a report is printed to the user
 * Most new code is the function to print tables (used by `history` and `contexts`).


## 1.0.2

Tasks's creation date wasn't stored in the JSON data-file. This wasn't critical because the sort was working properly anyway. The tasks were stored in an array to which each new task was appended. This array was therefore sorted by the creation date, which allowed the sort to work properly.

At initialization, tasks had a default creation date set to NOW (the time the program executed). When exporting the tasks to the file, the program checks for each property whether the value is the default, in which case it considers that it's not necessary to export the value since it's the default anyway. When a new task was created, it was affected a creation date of NOW, which is the default, resulting in this creation date not being exported.

When tasks were sorted, the creation date criteria was futile since it was set for all tasks to NOW. However, since the sort is stable, it kept the original order of the array which is naturally sorted by creation date.

To fix the issue, the default creation date has been set to Python's datetime.datetime.min. From now on, new tasks have their creation date stored on the data-file. Old tasks aren't altered and are considered to be have been created at datetime.datetime.min after loading.

## 1.0.1

 * A single task visibility is now able to override its context visibility
 * UTF-8 encoding for the JSON data-file
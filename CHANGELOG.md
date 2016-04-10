## 2

New template for command-line interface: `todo <command> <value> [<options>]`. The features of v1 are usable thanks to the following commands:

 - `add <content> [<options>]` to add a task

 - `done <task_id>` to mark a task as done using its ID

 - `show [<context>]` to show the tasks of a given context. If no context is given then the behavior is the same as a bare `todo`

 - `task <task_id> <options>` to apply option(s) to an existing task using its ID

 - `ctx <context> [<options>]` to apply option(s) to a context using its name.

New features

 - `contexts`: lists all contexts ever used in the history of tasks, each one being displayed with its properties and the number of tasks this context currently has (including tasks belonging to subcontexts of this context)

 - `history`: shows full task history, including task that have been done

 - `rm <task_id>`: removes a task from history thanks to its ID.

 - `purge`: removes all task marked as done

Development:

 - Usage of the `docopt` module to parse argument instead of Python built-in argparse

 - Exportation of some utility function to an `utils.py` module and restructuration of the project under a Python package

 - Contexts have now their own class, which heritates with Task from a HasDefaults super class

 - Command-line arguments are parsed and transformed into objects. If a value type is unexpected, a report is printed to the user

 - Most new code is the function to print tables (used by `history` and `contexts`).


#### 1.0.2

Bugfix: tasks's creation date wasn't stored in the JSON data-file. This wasn't critical because the sort was working properly anyway. The tasks were stored in an array to which each new task was appended. This array was therefore sorted by the creation date, which allowed the sort to work properly.

At initialization, tasks had a default creation date set to NOW (the time the program executed). When exporting the tasks to the file, the program checks for each property whether the value is the default, in which case it considers that it's not necessary to export the value since it's the default anyway. When a new task was created, it was affected a creation date of NOW, which is the default, resulting in this creation date not being exported.

When tasks were sorted, the creation date criteria was futile since it was set for all tasks to NOW. However, since the sort is stable, it kept the original order of the array which is naturally sorted by creation date.

To fix the issue, the default creation date has been set to Python's datetime.datetime.min. From now on, new tasks have their creation date stored on the data-file. Old tasks aren't altered and are considered to be have been created at datetime.datetime.min after loading.

#### 1.0.1

 -  Bugfix: a single task visibility is now able to override its context visibility

 - UTF-8 encoding for the JSON data-file
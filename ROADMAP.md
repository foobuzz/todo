Roadmap
=======


## Housekeeping

## Patches

## Features

### v2

New template for command-line interface: `todo <command> <value> [<options>]`. The features of v1 will be usable thanks to the following commands:

 - `add <content> [<options>]` to add a task

 - `done <task_id>` to mark a task as done using its ID

 - `show [<context>]` to show the tasks of a given context. If no context is given then the behavior is the same as a bare `todo`

 - `task <task_id> <options>` to apply option(s) to an existing task using its ID

 - `context <context> [<options>]` to apply option(s) to a context using its name. New in v2: if no option is given then it shows the properties of the context (visibility and priority)

In addition, new features are planned with their associated commands:

 - `contexts`: lists all contexts ever used in the history of tasks, each one being displayed with its properties and the number of tasks this context currently has (including tasks belonging to subcontexts of this context)

 - `history`: shows full task history, including task that have been done

 - `rm <task_id>`: removes a task from history thanks to its ID.

 - `purge`: removes all task marked as done

### v?

The behavior of these features is to be specified in greater details before doing anything

 - Desktop notification when the deadline of a task approaches, for desktop environments supporting notifications. This should be customizable, and optional

 - Periodical tasks: make the same task repeat every N unit of time

 - API
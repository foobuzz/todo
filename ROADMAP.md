Roadmap
=======


## Housekeeping

 - Functional tests

 - Tables of contents in the README

## Patches

## Features

### v1.2

 - A positional argument to select a context in place of the `-c` option. Instead of running `todo -c watchlist` we would run `todo watchlist`. Contexts mutators will also work with such selector. The old `c`/`context̀̀` option will be kept for the sake of backward compatibility

 - Consulting the properties of a context (visibility and priority) using the `--infos` option with a context selector

 - Listing all contexts ever used in the history of tasks, each one being displayed with its properties and the number of tasks this context currently has (including tasks belonging to subcontexts of this context)

 - Showing full task history, including task that have been done

 - Removing a task from history thanks to its ID.

 - Removing all task "done" in bulk using the `--purge` option

### v?

The behaviour of these features is to be specified in greater details before doing anything

 - Desktop notification when the deadline of a task approaches, for desktop environments supporting notifications. This should be customizable, and optional

 - Periodical tasks: make the same task repeat every N unit of time

 - API
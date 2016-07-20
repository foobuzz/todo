Reference
=========

 * [Command-line usage](#command-line-usage)
 * [Configuration](#configuration)

## Command-line usage

### `todo [<context>]`

Print undone tasks that have started and that are visible from the given context, which defaults to the root context.

Tasks are sorted in the following order:

 1. Priority, descending
 2. Remaining time, ascending
 3. Context priority, descending
 4. Date added, ascending

Whether a task is visible from the given context is determined according to the task's visibility:

 - An `hidden` task is visible only from its context

 - A `discreet` task is visible from all contexts ascending from its context, excluding the root context

 - A `wide` task is visible from all contexts ascending from its context, including the root context

**Note:** If `<context>` happens to be the name of one of the built-in todo command, then you can use `todo ctx <context>` instead.


### `todo add <content> [--deadline MOMENT] [--start MOMENT] [--context CONTEXT] [--priority PRIORITY] [--visibility VISIBILITY]`

Add a task described by the given `<content>` and apply to it the options:

#### `-d --deadline MOMENT`

Define a dealine for the task. MOMENT can be a specific moment in time, in the following format:

 - YYYY-MM-DD

 - YYYY-MM-DDTHH:MM:SS

It can also be a delay, such as `2w` which means "2 weeks from now". Other accepted characters are `s`, `m`, `h`, `d`, `w`, which respectively correspond to seconds, minutes, hours, days and weeks. An integer must preeced the letter.

A task with no deadline is considered to have a deadline set to infinity.


#### `-s --start MOMENT`

Set the time at which a task starts. Non-started tasks aren't printed in the todolist. `MOMENT` uses the same format that with the `--deadline` option.

By default, a task starts at the moment it is created.


#### `-c --context CONTEXT`

The path of the context the task belongs to. It's a sequence of string separated by dots where each string indicate the name of a context in the contexts arborescence.

Any necessary new contexts will be created automatically.

By default, a task is associated to the root context.


#### `-p --priority PRIORITY`

An integer indicating the priority of the task. The highest the integer the highest the priority.

By default, a task has a priority of 1.


#### `-v --visibility VISIBILITY`

The visibility of a task. One of the following: `hidden`, `discreet` or `wide`.


### `todo done <id>`

Set the task identified by `id` as done. The ID of a task is shown at its left in lists output by `todo`.


### `todo task <id> [--deadline MOMENT] [--start MOMENT] [--context CONTEXT] [--priority PRIORITY] [--visibility VISIBILITY] [--text CONTENT]`

Apply the given options to the task identified by `id`. Options are described in the  `todo add` parts, with the addition of:

#### `-t --text CONTENT`

Overwrite the description of a task with `CONTENT`


### `todo edit <id>`

Open the text editor with a file containing the description of the task identified by `<id>`. Update the description of the task with the content of the file upon closing the editor.

The editor used can be configured. See Configuration.


### `todo history`

Print the list of all tasks sorted by creation date, along with their properties.


### `todo rm <id>...`

Remove tasks identified by the given `<id>`s (separated by spaces) from history.


### `todo purge`

Remove all done task from history.


### `todo ctx <context> [--priority PRIORITY] [--visibility VISIBILITY]`

If no option is given, has the same effect of `todo <context>`.

If at least one option is given, apply the option to the context. `--priority` sets the priority of the context (an integer). `--visibility` set the visibility of a context. The visibility of a context serves as the visibility of all the tasks belonging to this context in the case that the task has a default visibility.


### `todo --version`

Print current version.


### `todo --help`

Print basic help.


### `todo --location`

Print the path of the file containing the todolist. In most cases, the location should be `~/.toduh/data.json`. However, it's possible to set a different todolist for a working directory, by creating a folder named `.toduh` inside it.


## Configuration

Configuration is done by editing a configuration file which sits at `~/.toduhrc`. It should already exist and contain a template even if you never touched it.

The configuration file is in the INI format. It's made of sections, each of which is introduced by a `[Title]` enclosed in brackets. The lines of a section consist of `key = value` pairs. As a todo-specific convention, sections' title are capitalized while keys are all lower-case.

What follows is an exhaustive list of all sections recognized, and for each section, a table of all keys recognized, the fashion with which their value should be formatted and the defalt value.

### `[App]`

Key           |  Behavior                                                                                        |  Value format                                                                                               |  Example of value  |  Default value                                 
--------------|--------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------|--------------------|-------------------------------------------------
`editor`      |  Select the editor to use with `todo edit <id>`                                                  |  The name of the command to launch the text-editor. The command should accept a filename as first argument  |  `emacs`           |  None (fallback to vi is no configuration found)
`show_after`  |  Print the todolist again after completion of one a listed command, using the last used context  |  A list of todo built-in commands, separated by commas (optionally followed by a space)                     |  `done, edit`      |  `edit`                                         

### `[Colors]`

Key         |  Behavior                    |  Value format               |  Example of value  |  Default value
------------|------------------------------|-----------------------------|--------------------|---------------
`colors`    |  Turns coloring on or off    |  `on` or `off`              |  `on`              |  `on`         
`palette`   |  Chose how to diplay colors  |  `8`, `xterm-256` or `rgb`  |  `8`               |  `8`          
`id`        |  Color for tasks' id         |  Color-format*              |  `yellow`          |  `yellow`     
`context`   |  Color for context           |  Color-format*              |  `cyan`            |  `cyan`       
`deadline`  |  Color for deadline          |  Color-format*              |  `cyan`            |  `cyan`       
`priority`  |  Color for priority          |  Color-format*              |  `green`           |  `green`      

#### Color-format

Colors can be defined in multiple way:

 * One of the following: `black`, `red`, `green`, `yellow`, `blue`, `magenta`, `cyan`, `white`
 * An integer between 0 and 255, according to [the xterm color palette](http://www.calmar.ws/vim/256-xterm-24bit-rgb-color-chart.html)
 * `rgb(R,G,B)` where R, G and B are integers between 0 and 255 in their decimal representation
 * `#RRGGBB`where RR, GG, BB are integers between 0 and 255 in their hexadecimal representation

All formats work with any palette used, as necessary conversions will be made automatically.
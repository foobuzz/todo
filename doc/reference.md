Reference
=========

 * [Command-line usage](#command-line-usage)
 * [Configuration](#configuration)

## Command-line usage

### `todo [<context>] [--flat|--tidy]`

Print undone tasks that have started and that are in the given context, which defaults to the root context (identified by the empty string).

The `--flat` or `--tidy` option indicates whether subcontexts are listed below tasks (tidy) or whether tasks of subcontexts are integrated with general tasks (flat). If no such option is specified the configuration value is used (which defaults to tidy).

Tasks are sorted in the following order:

 1. Priority, descending
 2. Remaining time, ascending
 3. Context priority, descending
 4. Date added, ascending

Subcontexts are sorted in the following order:

 1. Priority, descending
 2. Total number of tasks (including in the descendance), descending

**Note:** If `<context>` happens to be the name of one of the built-in todo command, then you can use `todo ctx <context>` instead.


### `todo add <title> [--deadline MOMENT] [--start MOMENT] [--context CONTEXT] [--priority PRIORITY]`

Add a task titled `<title>` and apply to it the options:

#### `-d --deadline MOMENT`

Define a dealine for the task. MOMENT can be a specific moment in time, in the following format:

 - YYYY-MM-DD

 - YYYY-MM-DD HH:MM:SS

 - YYYY-MM-DDTHH:MM:SS

It can also be a delay, such as `2w` which means "2 weeks from now". Other accepted characters are `s`, `m`, `h`, `d`, `w`, which respectively correspond to seconds, minutes, hours, days and weeks. An integer must preeced the letter.

A task with no deadline is considered to have a deadline set to infinity.


#### `-s --start MOMENT`

Set the time at which a task starts. Non-started tasks aren't printed in the todolist. `MOMENT` uses the same format that with the `--deadline` option.

By default, a task starts at the moment it is created.


#### `-c --context CONTEXT`

The path of the context the task belongs to. It's a sequence of strings separated by dots where each string indicate the name of a context in the contexts hierarchy.

Any intermediary contexts will be created automatically.

By default, a task is associated to the root context.

**Note:** The root context having the empty string as name, the path of any subcontext formally start with a . (separating the empty string from the name if the first subcontext). However, for user convenience, the starting dot is optional.


#### `-p --priority PRIORITY`

An integer indicating the priority of the task. The highest the integer the highest the priority.

By default, a task has a priority of 1.


### `todo done <id>...`

Set the tasks identified by `id`s as done. The ID of a task is shown at its left in lists output by `todo`.


### `todo task <id> [--deadline MOMENT] [--start MOMENT] [--context CONTEXT] [--priority PRIORITY] [--title TITLE]`

Without any option, print the contents of the task (its metadata followed by its body).

With at least one option: apply the given options to the task identified by `id`. Options are described in the  `todo add` parts, with the addition of:

#### `-t --title TITLE`

Overwrite the title of a task with `TITLE`


### `todo edit <id>`

Open the text editor with a file containing the description of the task identified by `<id>`. Update the description of the task with the content of the file upon closing the editor.

The editor used can be configured. See [Configuration](#configuration).


### `todo history`

Print the list of all tasks sorted by creation date, along with their properties.


### `todo search <term> [--context CONTEXT] [--done|--undone] [--before MOMENT] [--after MOMENT] [--case]`

Search for tasks whose title contains the substring `<term>`. The search is case unsensitive, unless the `--case` flag is set. The flag `--done` (resp. `--undone`) restricts the search to done (resp. undone) tasks. You can select a segment of time in which searching the tasks (by their creation date), `MOMENT` being in same the format than other `MOMENT`s (deadlines, etc).

**Note:** if you want to perform an advanced search using regular expressions and such, use this command with the empty string for `<term>`, which will print all tasks matching the other options, and pipe the output to `grep` to do custom filtering on titles


### `todo rm <id>...`

Remove tasks identified by the given `<id>`s (separated by spaces) from history.


### `todo purge [--force] [--before MOMENT]`

Remove done tasks from history that were created before `MOMENT`. Ask the user for confirmation, unless the `--force` flag is given.

**Note:** `MOMENT` is in the same format than for `--deadline`. Of course, if a delay is given such as `2w` it means "two weeks ago" (in the past) and not "in two weeks".


### `todo ctx <context> [--flat|--tidy] [--priority PRIORITY] [--visibility VISIBILITY] [--name NAME]`

If no mutation option is given, has the same effect than `todo <context>`.

If at least one mutation option is given, apply the option to the context and prints nothing.

`--name` renames the context. In the context's path, the name of the context is the last part among parts separated by dots. For example, renaming `culture.movies` with `films` will lead to the new path `culture.films`. An error is printed if the new name contains a dot or if the destination context already exists.


### `todo mv <ctx1> <ctx2>`

Move all tasks and subcontexts from `<ctx1>` to `<ctx2>`. Any necessary new context is created.


### `todo rmctx <context> [--force]`

Remove the context `<context>`, including all of its tasks (done and undone) and subcontexts recursively. Ask the user for confirmation, unless the `--force` flag is given.


### `todo --version`

Print current version.


### `todo --help`

Print basic help.


### `todo --location`

Print the path of the data directory. By default, the location is `~/.toduh`. However, it's possible to set a different dataset for a specific directory, by creating a folder named `.toduh` inside it and then calling todo from this directory.


## Configuration

Configuration is done by editing a configuration file which sits at `~/.toduhrc`.

The configuration file is in the INI format. It's made of sections, each of which is introduced by a `[Title]` enclosed in brackets. The lines of a section consist of `key = value` pairs. As a todo-specific convention, sections' title are capitalized while keys are all lower-case.

What follows is an exhaustive list of all sections recognized, and for each section, a table of all keys recognized, the fashion with which their value should be formatted and the defalt value.

### `[App]`

Key           |  Behavior                                                                                        |  Value format                                                                                               |  Default value                                 
--------------|--------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------|-------------------------------------------------
`editor`      |  Select the editor to use with `todo edit <id>`                                                  |  The name of the command to launch the text-editor. The command should accept a filename as first argument  |  None (fallback to the `EDITOR` environment variable if no configuration found; fallback to vim if no env variable found)                                
`layout`      |  Select the layout for the `todo` command  |  `basic` or `multiline`  |  `basic`
`todo_fashion`|  Sets the `--flat` or `--tidy` option of the `todo` command by default                           |  `flat` or `tidy`                                                                                           |  `tidy`
`show_empty_contexts` |  Whether empty subcontexts should be listed when running `todo`                      | `on` or `off`                                                                                               |  `on`

### `[Colors]`

Key         |  Behavior                    |  Value format               |  Default value
------------|------------------------------|-----------------------------|---------------
`colors`    |  Turns coloring on or off    |  `on` or `off`              |  `on`         
`palette`   |  Chose how to diplay colors  |  `8`, `xterm-256` or `rgb`  |  `8`          
`id`        |  Color for tasks' id         |  Color-format*              |  `yellow`     
`context`   |  Color for context           |  Color-format*              |  `cyan`       
`deadline`  |  Color for deadline          |  Color-format*              |  `cyan`       
`priority`  |  Color for priority          |  Color-format*              |  `green`      

#### Color-format

Colors can be defined in multiple way:

 * One of the following: `black`, `red`, `green`, `yellow`, `blue`, `magenta`, `cyan`, `white`
 * An integer between 0 and 255, according to [the xterm color palette](http://www.calmar.ws/vim/256-xterm-24bit-rgb-color-chart.html)
 * `rgb(R,G,B)` where R, G and B are integers between 0 and 255 in their decimal representation
 * `#RRGGBB`where RR, GG, BB are integers between 0 and 255 in their hexadecimal representation

All formats work with any palette used, as necessary conversions will be made automatically.


### `[Word-wrapping]`

Key      |  Behavior  |  Value format  |  Default value
---------|------------|----------------|-----------------
`title`  | Enable word-wrapping for tasks' titles in `todo` listing | `on` or `off` | `on`
`content` | Enable word-wrapping for tasks' content in `todo task <id>` output | `on` or `off` | `on`
`smart`  | Enable "smart" word-wrapping for Markdown content (experimental) | `on` or `off` | `off`
`width` | Width to use for word-wrapping | integer | `-1` (means: use current terminal width)

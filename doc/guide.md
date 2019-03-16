User guide
==========

  * [Basic Usage](#basic-usage)
  * [Deadlines](#deadlines)
    * [Long-term scheduling](#long-term-scheduling)
  * [Priority](#priority)
  * [Contexts](#contexts)
    * [Subcontexts](#subcontexts)
    * [Visibility](#visibility)
    * [Context priority](#context-priority)
  * [Sort summary](#sort-summary)
  * [History](#history)
  * [Configuration](#configuration)
    * [App](#app)
    * [Colors](#colors)


## Basic usage

Add a task to do using the `add` command:

	$ todo add "Do the thing"

See what you have to do by passing no option:

	$ todo
	    1 | Do the thing

The tasks shown first are the ones you entered first:

	$ todo add "Fix the stuff"
	$ todo
	    1 | Do the thing
	    2 | Fix the stuff

Set a task as done using the `done` command, with the task's ID as value:

	$ todo done 1
	$ todo
	    2 | Fix the stuff


## Deadlines

Set a deadline to a task using the `-d` or `--deadline` option. The value is a date in the `YYYY-MM-DD` or `YYYY-MM-DD HH:MM:SS` format:

	$ todo add "Buy the gift for Stefany" --deadline 2016-02-25
	$ todo
	    3 | Buy the gift for Stefany ⌛ 16 days remaining
	    2 | Fix the stuff

Tasks with a deadline show up before tasks with no deadline, and tasks with closer deadlines are shown first. In the following example, a deadline is set using a delay instead of a date. Delays are specified using the letters `s`, `m`, `h`, `d`, `w` which respectively correspond to seconds, minutes, hours, days and weeks.

	$ todo add "Send the documents for the house" --deadline 1w
	$ todo
	    4 | Send the documents for the house ⌛ 6 days remaining
	    3 | Buy the gift for Stefany ⌛ 16 days remaining
	    2 | Fix the stuff

### Long-term scheduling

Let's schedule the buying of a fireworks package for the 4th of July:

	$ todo add "Buy the fireworks package" --deadline 2016-07-04
	$ todo 
	    4 | Send the documents for the house ⌛ 6 days remaining
	    3 | Buy the gift for Stefany ⌛ 16 days remaining
	    5 | Buy the fireworks package ⌛ 146 days remaining
	    2 | Fix the stuff

Since it's a long-term task, you probably don't want it to be shown in the middle of tasks that need to be done quickly.

You can use the `-s` or `--start` option in order to set a start-point to the task. The task will show up in the todolist only starting from the start-point. The value of `-s` is in the same format than for `--deadline`: a date or a delay. Let's say we want to be bothered by the fireworks thing starting from the middle of June.

	$ todo task 5 -s 2016-06-15
	$ todo
	    4 | Send the documents for the house ⌛ 6 days remaining
	    3 | Buy the gift for Stefany ⌛ 16 days remaining
	    2 | Fix the stuff

The task won't show up until 2016-06-15.

In this example, we used the `task` command to select a task to apply a modifier to. All the modifiers available when creating a task with the `add` command are also available when selecting a task with the `task` command.

## Priority

You can assign a priority to a task using the `-p` or `--priority` option. Priorities are integers; the higher the integer, the higher the priority. Tasks with a higher priority are shown first. By default, tasks have a priority of 1.

	$ todo add "Fix the window" -p 3
	$ todo
	    6 | Fix the window ★3
	    4 | Send the documents for the house ⌛ 6 days remaining
	    3 | Buy the gift for Stefany ⌛ 16 days remaining
	    2 | Fix the stuff
	$ todo task 2 -p 2
	$ todo
	    6 | Fix the window ★3
	    2 | Fix the stuff ★2
	    4 | Send the documents for the house ⌛ 6 days remaining
	    3 | Buy the gift for Stefany ⌛ 16 days remaining

## Contexts

You can put the task in a context using the `-c` or `--context` option. Contexts are strings.

	$ todo add "Read the article about chemistry" -c culture
	$ todo
	    6 | Fix the window ★3
	    2 | Fix the stuff ★2
	    4 | Send the documents for the house ⌛ 6 days remaining
	    3 | Buy the gift for Stefany ⌛ 16 days remaining
	----------------------------------------
	    # | culture (1)

You can think of contexts as directories in which you put tasks. Contexts are listed after the list of tasks, and the number of tasks of each context is indicated.

To see the todolist of a specific context, you need to indicate the name of the context:

	$ todo culture
	    7 | Read the article about chemistry

Another way to accomplish that is though the `ctx` command:

	$ todo ctx culture
	    7 | Read the article about chemistry #culture

This helps removing any ambiguity if you ever have a context whose name happens to be the name of a command (a command wins over a context).

You can also display tasks of contexts integrated with general tasks with the `--flat` option:

	$ todo --flat
	    6 | Fix the window ★3
	    2 | Fix the stuff ★2		
	    4 | Send the documents for the house ⌛ 6 days remaining
	    3 | Buy the gift for Stefany ⌛ 16 days remaining
	    7 | Read the article about chemistry #culture

Notice how the `#` flag indicates the context of the task. You can set the `--flat` option to be the default way to display tasks in the [configuration file](https://github.com/foobuzz/todo/blob/master/doc/reference.md#configuration). In such case, the original hierarchical display is achieved using the `--tidy` option.


### Subcontexts

Since contexts are equivalent to directories, you can also create a hierarchy of contexts. You can define contexts within contexts using the dot notation:

	$ todo task 7 -c culture.chemistry
	$ todo culture
	----------------------------------------
	 # | chemistry (1)
	$ todo add "Listen to the podcast about movies" -c culture.cinema
	$ todo culture
	----------------------------------------
	 # | chemistry (1)
	 # | cinema (1)
	$ todo culture.chemistry
	 7 | Read the article about chemistry
	$ todo culture --flat
	 7 | Read the article about chemistry #chemistry
	 8 | Listen to the podcast about movies #cinema
	$ todo --flat
	 6 | Fix the window ★3
	 2 | Fix the stuff ★2
	 4 | Send the documents for the house ⌛ 6 days remaining
	 3 | Buy the gift for Stefany ⌛ 16 days remaining
	 7 | Read the article about chemistry #culture.chemistry
	 8 | Listen to the podcast about movies #culture.cinema


### Visibility

Contexts have a visibility which is either `normal` or `hidden`. Hidden contexts aren't shown when using `todo` on their parent context. However, they still exists and their tasks can be seen as regular contexts by doing `todo <context>`.

	$ todo ctx culture --visibility hidden
	$ todo
	 6 | Fix the window ★3
	 2 | Fix the stuff ★2		
	 4 | Send the documents for the house ⌛ 6 days remaining
	 3 | Buy the gift for Stefany ⌛ 16 days remaining
	$ todo ctx culture -v normal
	$ todo
	 6 | Fix the window ★3
	 2 | Fix the stuff ★2		
	 4 | Send the documents for the house ⌛ 6 days remaining
	 3 | Buy the gift for Stefany ⌛ 16 days remaining
	----------------------------------------
	 # | culture (2)


### Context priority

You can specify a priority to a context:

	$ todo ctx culture -p 10
	$ todo
	 6 | Fix the window ★3
	 2 | Fix the stuff ★2		
	 4 | Send the documents for the house ⌛ 6 days remaining
	 3 | Buy the gift for Stefany ⌛ 16 days remaining
	----------------------------------------
	 # | culture (2) ★10

When doing a `todo`, contexts are sorted by:
 * Priority, descending
 * Number of tasks, descending

[More about contexts: how to rename contexts, delete contexts, move all tasks from one context to another, list all existing contexts](https://github.com/foobuzz/todo/blob/master/doc/reference.md#todo-ctx-context---flat--tidy---priority-priority---visibility-visibility---name-name)


## Editing

Once a task has been created, you can edit its content using the `edit` command:

	$ todo edit 1

This opens a text editor with the content of the task. Upon saving and quitting the editor, the task's content is updated.

The text displayed in `todo`'s listing is actually only the title of the task. You can add any arbitrary content to the task by underlining the title with equal signs (`=`) and writing more text after it. For example, with such text:

	Do the thing
	============

	Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.

Only the title `Do the thing` will appear in the task listing. This way of highlighting a title from the rest of the text is called a *settext header* in the [Markdown](https://en.wikipedia.org/wiki/Markdown) format. If you want to read the entire content of a given task, you can simply use the `task` command:

	$ todo task 1
	     ID: 1
	Created: 2019-03-16 16:14:37
	  Start: @created
	 Status: TODO
	-------------------------------------------------------------------------------------
	Do the thing
	============

	Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor
	incididunt ut labore et dolore magna aliqua.

This command first prints a bunch of metadata about the task, then its contents. When using this command, the body of the task is [word-wrapped](https://en.wikipedia.org/wiki/Line_wrap_and_word_wrap) to fit in your terminal. 


## Sort summary

When showing the todolist, tasks are sorted in the following order:

 * Priority, descending
 * Remaining time, ascending
 * Context priority, descending
 * Date added, ascending


## More

Find out more commands and details in the [Reference](https://github.com/foobuzz/todo/blob/master/doc/reference.md).


## Configuration

Configuration is done by editing a configuration file which sits at `~/.toduhrc`.

The configuration file is in the INI format. It's made of sections, each of which is introduced by a `[Title]` enclosed in brackets. The lines of a section consist of `key = value` pairs.


### App

The App section contains general parameter for the application. Most notably, `editor` indicates the editor to use with the `edit` command. The name given should be the command used to run the editor via the command-line. This command should accept a filename to open as first argument. `vi` and `emacs` are examples of editors working this way.


### Colors

The Colors section allow you to customize colors.

The `colors` key should have either `on` or `off` for value. It indicates whether todo should use colors at all.

Example:

	colors = off

This turns coloring off.

The `palette` key indicates how to print the colors. 3 values are recognized:

 - `8` instruct to use a palette of 8 colors

 - `xterm-256` instruct to use the xterm color palette, made of 256 colors

 - `rgb` instruct to use true colors

Support for these palettes varies among terminals. `8` is supported virtually everywhere, `xterm-256` on xterm, `rgb` only on some advanced terminals. Using a palette not supported by your terminal can result in no color at all, wrong colors, or scrambled text. The default is `8`.

The following keys can be used to customize the color of the different parts of the `todo` command output: `id`, `context`, `deadline` and `priority`. Accepted values for colors are described in the [Reference](https://github.com/foobuzz/todo/blob/master/doc/reference.md#color-format

Here's an example of a complete configuration file:

**~/.toduhrc**

	[App]
	editor = emacs

	[Colors]
	colors = on
	palette = xterm-256

	id = yellow
	context = cyan
	deadline = cyan
	priority = green
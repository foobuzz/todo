User guide
==========

 * [Documentation](#documentation)
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
 * [Reference](#reference)
 * [Contributing](#contributing)
  * [Tests](#tests)


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

Set a deadline to a task using the `-d` or `--deadline` option. The value is a date in the YYYY-MM-DD format:

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

You can use the `-s` or `--start` option in order to set a start-point to the task. The task will show up in the todo list only starting from the start-point. The value of `-s` is in the same format than for `--deadline`: a date or a delay. Let's say we want to be bothered by the fireworks thing starting from the middle of June.

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

You can assign a context to a task using the `-c` or `--context` option. Contexts are strings.

	$ todo add "Read the article about chemistry" -c culture
	$ todo
	    6 | Fix the window ★3
	    2 | Fix the stuff ★2
	    4 | Send the documents for the house ⌛ 6 days remaining
	    3 | Buy the gift for Stefany ⌛ 16 days remaining
	    7 | Read the article about chemistry #culture

To filter tasks according to their context, you need to indicate the name of the context:

	$ todo culture
	    7 | Read the article about chemistry #culture

Another way to accomplish that is though the `ctx` command:

	$ todo ctx culture
	    7 | Read the article about chemistry #culture

This helps removing any ambiguity if you ever have a context whose name happens to be the name of a command.

### Subcontexts

You can define contexts within contexts using the dot notation:

	$ todo task 7 -c culture.chemistry
	$ todo ctx culture
	    7 | Read the article about chemistry #chemistry
	$ todo add "Listen to the podcast about movies" -c culture.cinema
	$ todo ctx culture
	    7 | Read the article about chemistry #chemistry
	    8 | Listen to the podcast about movies #cinema
	$ todo ctx culture.chemistry
	    7 | Read the article about chemistry

### Visibility

Tasks have a visibility which impacts on what tasks are listed when you use the `todo` command with a context's name. There are three kinds of visibility: hidden, discreet or wide. The default is discreet.

 - hidden means that the task will show up only if its context is exactly the one given in the command line. So `hello.world.yeah` will only match `hello.world.yeah`.

 - discreet means that the task will show up only if its context is a subcontext of the one given in the command line. `hello.world.yeah` is a subcontext of `hello.world` and also a subcontext of `hello`. Discreet tasks which have a top-level context will also show up when a bare `todo` is ran, such as `culture` in the previous examples.

 - wide is the same as discreet, but the task will always show up when no context is specified in the command line, even if the task doesn't have a top-level context.

For example, continuing on the previous example, if you show the general todolist:

	$ todo
	    6 | Fix the window ★3
	    2 | Fix the stuff ★2
	    4 | Send the documents for the house ⌛ 6 days remaining
	    3 | Buy the gift for Stefany ⌛ 11 days remaining

You realize that the cultural tasks have disappeared. That's because these tasks don't have a top-level context. They have sub-level contexts, namely `culture.chemistry` and `culture.movies`. Being discreet by default, these tasks will only show up when you query the todolist with a super-context of their context, `culture` in this case:

	$ todo culture
	    7 | Read the article about chemistry #culture.chemistry
	    8 | Listen to the podcast about movies #culture.cinema

If you really want them to be shown in the general todolist, you can set their visibility to "wide", using the `-v` or `--visibility` option:

	$ todo task 7 -v wide
	$ todo task 8 -v wide
	$ todo
	    6 | Fix the window ★3
	    2 | Fix the stuff ★2
	    4 | Send the documents for the house ⌛ 6 days remaining
	    3 | Buy the gift for Stefany ⌛ 11 days remaining
	    7 | Read the article about chemistry #culture.chemistry
	    8 | Listen to the podcast about movies #culture.cinema

On the opposite, if you want a task to appear only if you query the todolist with its exact context, you can set its visibility to "hidden".

	$ todo task 7 -v hidden
	$ todo
	    6 | Fix the window ★3
	    2 | Fix the stuff ★2
	    4 | Send the documents for the house ⌛ 6 days remaining
	    3 | Buy the gift for Stefany ⌛ 11 days remaining
	    8 | Listen to the podcast about movies #culture.cinema
	$ todo culture
	    8 | Listen to the podcast about movies #cinema
	$ todo culture.chemistry
	    7 | Read the article about chemistry

You can specify the visibility of a context. This visibility will apply to all tasks belonging to the context that have the default visibility (discreet). If a task has a non-default visibility, it'll override the visibility of its context.

	$ todo ctx culture.cinema -v wide

This only applies to tasks which match the exact context, this doesn't recurse to subcontexts.

### Context priority

You can specify a priority to a whole context:

	$ todo ctx health -p 10

Tasks with this context will always show up before tasks with a lower context priority.


## Sort summary

When showing the todolist, tasks are sorted in the following order:

 * Priority, descending
 * Remaining time, ascending
 * Context priority, descending
 * Date added, ascending


## History

There are several commands to help you browse the history of your tasks.

The command `history` shows the list of tasks sorted by chronological order, including tasks marked as done:

	$ todo history
	 id content                                    created    context        status 
	--- ------------------------------------------ ---------- -------------- -------
	  1 Do the thing                               2016-04-09                DONE   
	  2 Fix the stuff                              2016-04-09                       
	  3 Buy the gift for Stefany                   2016-04-09                       
	  4 Send the documents for the house           2016-04-09                       
	  5 Buy the fireworks package                  2016-04-09                       
	  6 Fix the window                             2016-04-09                       
	  7 Read the article about chemistry           2016-04-09 culture.che...        
	  8 Listen to the podcast about movies         2016-04-09 culture.cinema        

Notes:

 * Don't mind the dates not being consistent with the rest of the README
 * Prior to version 1.0.2, tasks' creation date wasn't stored. Tasks created prior to this version will have a blank value in the "created" column
 * The `history` command adapts according to the width of the terminal. If you make your terminal wider, more columns are shown with more info.

To definetely remove a task from history, use the `rm` command with the task's id:

	$ todo rm 3
	$ todo history
	 id content                                    created    context        status 
	--- ------------------------------------------ ---------- -------------- -------
	  1 Do the thing                               2016-04-09                DONE   
	  2 Fix the stuff                              2016-04-09                       
	  4 Send the documents for the house           2016-04-09                       
	  5 Buy the fireworks package                  2016-04-09                       
	  6 Fix the window                             2016-04-09                       
	  7 Read the article about chemistry           2016-04-09 culture.che...        
	  8 Listen to the podcast about movies         2016-04-09 culture.cinema        

To remove all tasks marked as done, use the `purge` command:

	$ todo purge
	$ todo history
	 id content                                    created    context        status 
	--- ------------------------------------------ ---------- -------------- -------
	  2 Fix the stuff                              2016-04-09                       
	  4 Send the documents for the house           2016-04-09                       
	  5 Buy the fireworks package                  2016-04-09                       
	  6 Fix the window                             2016-04-09                       
	  7 Read the article about chemistry           2016-04-09 culture.che...        
	  8 Listen to the podcast about movies         2016-04-09 culture.cinema        


To list all the contexts, use the `contexts` command.

	$ todo contexts
	context                                         visibility priority undone tasks
	----------------------------------------------- ---------- -------- ------------
	                                                                    6           
	culture                                                             2           
	culture.chemistry                                                   1           
	culture.cinema                                  wide                1           
	health                                                     10       0               

The first line is the "root context", which contains all tasks without any specific context and is the father of all contexts. The number of undone tasks shown include tasks in subcontexts, which means the first line displays the total number of undone tasks.

todo remembers a context if it meets one of the following conditions:

 * One of the tasks in history has such context
 * This context has a non-default property attached to it (visibility different than discreet or priority different than 1)

## Configuration

Configuration is done by editing a configuration file which sits at `~/.toduhrc`. It should already exist and contain a template even if you never touched it.

The configuration file is in the INI format. It's made of sections, each of which is introduced by a `[title]` enclosed in brackets. The lines of a section consist of `key = value` pairs.


### App

The App section contains general parameter for the application. Two keys are recognized:

`editor` indicates the editor to use with the `edit` command. The name given should be the command used to run the editor via the command-line. This command should accept a filename to open as first argument. `vi` and `emacs` are examples of editors working this way.

Example:

	editor = emacs

`show_after` is a list of todo built-in commands separated by commas. It indicates that after completing those commands, todo will print the todolist again, *using the last used context*.

Example:
	
	show_after = done

Then, using the application:

	$ todo myContext
	1 | some task
	2 | some other task

	$ todo done 1
	2 | some other task

By default, usage of the `done` command doesn't print the todolist again, but in this case it did because `done` is contained in the `show_after` list. Note that for printing the todolist again, the last used context, that is `myContext`, has been automatically used.

### Colors

The Colors section allow you to customize colors.

`colors` should have either `on` or `off` for values. It indicates whether todo should use colors at all, or not.

Example:

	colors = off

This turns coloring off.

`palette` indicates how to print the colors. 3 values are recognized:

 - `8` instruct to use the 8 primary colors

 - `xterm-256` instruct to use the xterm color palette, made of 256 colors

 - `rgb` instruct to use true colors

Support for these palettes varies among terminals. `8` is supported virtually everywhere, `xterm-256` on xterm, `rgb` only on some advanced terminals. Using a palette not supported by your terminal can result in no color at all, wrong colors, or scrambled text.

The following keys can be used to customize the color of the different parts of the `todo` command output: `id`, `context`, `deadline` and `priority`.


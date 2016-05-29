todo
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

*This is the README for version 2. Find the README for version 1 [here](https://github.com/foobuzz/todo/blob/master/doc/v1.md).*

# Installation

Install the `todocli` package for Python 3 via pip3.


# Table of contents

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


# Documentation


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
	    7 | Read the article about chemistry #culture.chemistry
	$ todo add "Listen to the podcast about movies" -c culture.cinema
	$ todo ctx culture
	    7 | Read the article about chemistry #culture.chemistry
	    8 | Listen to the podcast about movies #culture.cinema
	$ todo ctx culture.chemistry
	    7 | Read the article about chemistry #culture.chemistry

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
	    8 | Listen to the podcast about movies #culture.cinema
	$ todo culture.chemistry
	    7 | Read the article about chemistry #culture.chemistry

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

The first line is the "empty context", which contains all tasks without any specific context.

todo remembers a context if it meets one of the following conditions:

 * One of the tasks in history has such context
 * This context has a non-default property attached to it (visibility different than discreet or priority different than 1)


# Reference

	todo. CLI todo list manager.

	Usage:
	  todo [<context>]
	  todo add <content> [--deadline MOMENT] [--start MOMENT] [--context CONTEXT]
	    [--priority PRIORITY] [--visibility VISIBILITY]
	  todo done <id>
	  todo task <id> [--deadline MOMENT] [--start MOMENT] [--context CONTEXT]
	    [--priority PRIORITY] [--visibility VISIBILITY]
	  todo rm <id>
	  todo ctx <context> [--priority PRIORITY] [--visibility VISIBILITY]
	  todo contexts
	  todo history
	  todo purge
	  todo --help
	  todo --version
	  todo --location

	Options:
	  -d MOMENT, --deadline MOMENT            Set the deadline of a task
	  -s MOMENT, --start MOMENT               Set the start-line of a task
	  -c CONTEXT, --context CONTEXT           Set the context of a task
	  -p INTEGER, --priority INTEGER          Set the priority of a task, or of a
	                                          context
	  -v VISIBILITY, --visibility VISIBILITY  Set the visibility of a task, or of a
	                                          context.



# Contributing

Pull requests related to bugfixes, tests, documentation, security, performance, etc, are welcomed. It might be a good idea to discuss the problem they resolve in an issue beforehand if relevant.

[The Roadmap](https://github.com/foobuzz/todo/blob/master/ROADMAP.md) lists features I plan to work on when I have the time. If you'd like to develop one you can submit a pull request. Pull requests for features not in the Roadmap may or may not be merged.

I like documentation-driven development so in case you want to develop any feature I would like your pull request to be an update of the README in a first place. Once I validate it, you'll have green light for development and the request will be merged when the feature is fully implemented.


## Running a development version

To run the program in development, download the project's zip and go to the `source` directory. You can run the source by executing:

	python todo

If you create a file named `.dev` in the `todo` directory, then a new and independant datafile is used to store the tasks alongside the real application datafile.


## Tests

To run the tests, go the `source` directory and execute:

	python tests

By default, this only launches the unit tests. There is also a functional test. The fonctional test uses the file `tests/cmd_trace`. This file contains a list of commands (lines introduced by `$`), each above the standard output they should produce. The functional test runs each of the commands in a subprocess and compare their output to the expected output. The test is ran on a new datafile each time, which doesn't affect the regular datafile.

To run the functional test, use the `-f` option. The `-a` option runs both unit and functional tests. The `-v` option, when used with the functional test, prints the commands being executed.
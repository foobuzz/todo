#### 1.0.2

Bugfix: tasks's creation date wasn't stored in the JSON data-file. This wasn't critical because the sort was working properly anyway. The tasks were stored in an array to which each new task was appended. This array was therefore sorted by the creation date, which allowed the sort to work properly.

At initialization, tasks had a default creation date set to NOW (the time the program executed). When exporting the tasks to the file, the program checks for each property whether the value is the default, in which case it considers that it's not necessary to export the value since it's the default anyway. When a new task was created, it was affected a creation date of NOW, which is the default, resulting in this creation date not being exported.

When tasks were sorted, the creation date criteria was futile since it was set for all tasks to NOW. However, since the sort is stable, it kept the original order of the array which is naturally sorted by creation date.

To fix the issue, the default creation date has been set to Python's datetime.datetime.min. From now on, new tasks have their creation date stored on the data-file. Old tasks aren't altered and are considered to be have been created at datetime.datetime.min after loading.

#### 1.0.1

 -  Bugfix: a single task visibility is now able to override its context visibility

 - UTF-8 encoding for the JSON data-file
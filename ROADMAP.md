Roadmap
=======

## Features & Behaviour

 * Renaming contexts (`todo mv ctx1 ctx2`)
 * A tool for checking the consistency of the configuration file (`todo config --check`)
 * Indentation when running `todo contexts`
 * More verbose message when trying to mutate an non-existing task/context
 * Allow `todo task <id>` without any mutator and just print the task
 * Recurring tasks
 * Desktop notification when a deadline approaches


## Implementation

 * Find a faster alternative to `docopt` for argument parsing as it takes more than 50% of the executing time of the program
 * Find a faster/lightweight alternative to `configparser` for configuration parsing as it takes much time to import.
 * Putting done tasks in a separate file as they're only accessed by `history`, `rm` and `purge`, which are way less used than `todo` and `todo add`, etc
 * Change the way the data is stored: match the arborescence of contexts with the file-system arborescence


## To think about

 * Multiple machines
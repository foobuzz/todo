Roadmap
=======

### v2.1.1

 * Find a faster alternative to `docopt` for argument parsing as it takes more than 50% of the executing time of the program
 * Find a faster/lightweight alternative to `configparser` for configuration parsing as it takes much time to import.

### v?

 * Renaming contexts (`todo mv ctx1 ctx2`)
 * A tool for checking the consistency of the configuration file (`todo --check`)
 * Indentation when running `todo contexts`
 * More verbose message when trying to mutate an non-existing task/context
 * Putting done tasks in a separate file as they're only accessed by `history`, `rm` and `purge`, which are way less used than `todo` and `todo add`, etc
 * Allow `todo task <id>` without any mutator and just print the task
 * Recurring tasks
 * Desktop notification when a deadline approaches
-----
tasks
-----

Tools for developers, such as testing, building docs/website, etc.

Usage::
    
    invoke task ...
    invoke --help task

This makes use of the invoke package to translate CLI commands to function
calls. This package is set up so that new tasks can be added simply by adding
a module that defines one or more tasks, this makes it easy to share tasks
between projects.

Each project must implement its own _config.py, so that the tasks themselves
can be project-agnostic.

Names that you can `from ._config import ...`:

* NAME - the name of the project
* THIS_DIR - the path of the tasks directory
* ROOT_DIR - the root path of the repository
* DOC_DIR - the path to the docs
* DOC_BUILD_DIR - the path to where the docs are build
* ... - more may be added, depending on what tasks are present


License
-------

Consider this code public domain unless stated otherwise.

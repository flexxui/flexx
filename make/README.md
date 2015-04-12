----
make
----

Tools for developers, such as testing, building docs/website, etc.

Usage::
    
    python make command [arg]

Adding commands
---------------

To add a command, create a file `command.py` that defines a function
`command()` that accepts one optional argument. 

Shared code can be put in separate modules. Prepend modules that are
not commands with an underscore.

Names that you can `from make import ...`:

* NAME - the name of the project
* THIS_DIR - the path of the make directory
* ROOT_DIR - the root path of the repository
* DOC_DIR - the path to the docs
* DOC_BUILD_DIR - the path to where the docs are build
* TEST_DIR - root dir for tests
* ... - more may be added in the future


Using this code
---------------

If you want to use this method in your project, copy the `__init__.py`,
`__main__.py` and `help.py` in a directory called `make` in the root
of your repository, along with any other commands that you want.

In `__init__.py` you need to edit the `NAME` and perhaps some other
variables.

License
-------

Consider this code public domain unless stated otherwise.

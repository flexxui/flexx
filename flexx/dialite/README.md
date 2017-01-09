flexx.dialite subpackage
------------------------

Dialite is a lightweight Python package for cross-platform dialogs.
It provides a handful of functions, each one a verb, that can be
used to inform(), warn() or fail() the user, or to confirm() something
or ask() a yes-no question.

Dialite is pure Python, has no dependencies, and is written to work on
Python 3 and Python 2.x. It works on Windows (from at least XP), Linux
(most ones anyway, including Raspbian) and OS X.

Dialite provides a way to communicate with the user without needing a fancy
(and heavy) GUI library. It's also much easier to package with tools like
cx_Freeze.

Example:
```py
from flexx import dialite

dialite.ask('Troll question', 'Do you prefer VI over Emacs?')

dialite.confirm('Confirm download', 'Will now download the resources.')
```

""" Run tests.
* unit - run unit tests
* style - flake style testing (PEP8 and more)
"""

from make import ROOT_DIR, NAME, help


def test(arg):
   
    if not arg:
        return help('test')
    if arg == 'unit':
        import pytest
        pytest() # ...
    if arg == 'style':
        flake8()

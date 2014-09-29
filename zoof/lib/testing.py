import sys
import inspect

import pytest
from _pytest import runner
runner.pytest_runtest_call_orig = runner.pytest_runtest_call


def pytest_runtest_call(item):
    """ Variant of pytest_runtest_call() that stores traceback info for
    postmortem debugging.
    """
    try:
        runner.pytest_runtest_call_orig(item)
    except Exception:
        type, value, tb = sys.exc_info()
        tb = tb.tb_next  # Skip *this* frame
        sys.last_type = type
        sys.last_value = value
        sys.last_traceback = tb
        del tb  # Get rid of it in this namespace
        raise

# Monkey-patch pytest
runner.pytest_runtest_call = pytest_runtest_call


def run_tests_if_main():
    """ Run tests in a given file if it is run as a script
    """
    local_vars = inspect.currentframe().f_back.f_locals
    if not local_vars.get('__name__', '') == '__main__':
        return
    # we are in a "__main__"
    fname = local_vars['__file__']
    pytest.main('-v -x --color=yes %s' % fname)

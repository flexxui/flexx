"""
This is a test of tests. Test that the bothtester functionality does
what its supposed to do. Most imortantly, it should fail at the right
moments.
"""

from flexx.util.testing import run_tests_if_main, skipif, skip, raises
from flexx.event.both_tester import run_in_both, StdoutMismatchError

from flexx import event

loop = event.loop
logger = event.logger


def this_is_js():
    return False


class Person(event.Component):

    first_name = event.StringProp('John', settable=True)
    last_name = event.StringProp('Doe', settable=True)


##

@run_in_both(Person)
def func_ok1():
    """
    john doe
    john doe
    almar klein
    """
    p = Person()
    print(p.first_name, p.last_name)
    p.set_first_name('almar')
    p.set_last_name('klein')
    print(p.first_name, p.last_name)
    loop.iter()
    print(p.first_name, p.last_name)


def test_ok1():
    assert func_ok1()

##

@run_in_both()
def func_ok2():
    """
    bar
    ----------
    foo
    """
    if this_is_js():
        print('foo')
    else:
        print('bar')

@run_in_both()
def func_ok3():
    """
    bar
    """
    if this_is_js():
        print('foo')
    else:
        print('bar')

@run_in_both()
def func_ok4():
    """
    foo
    """
    if this_is_js():
        print('foo')
    else:
        print('bar')


def test_ok234():
    assert func_ok2()
    with raises(StdoutMismatchError):
        func_ok3()
    with raises(StdoutMismatchError):
        func_ok4()


##

@run_in_both(Person)
def func_fail():
    """
    john doe
    almar klein
    """
    p = Person()
    print(p.first_name, p.last_name)
    p.set_first_name('almar')
    p.set_last_name('klein')
    print(p.first_name, p.last_name)
    loop.iter()
    print(p.first_name, p.last_name)


def test_fail():
    with raises(StdoutMismatchError):
        func_fail()

##

@run_in_both()
def func_ok_exception():  # ? indicates that the following text must be present
    """
    ? AttributeError
    """
    try:
        raise AttributeError('xx')
    except Exception as err:
        logger.exception(err)


def test_ok_exception():
    assert func_ok_exception()


##

@run_in_both()
def func_fail_exception1():  # This just fails hard
    """
    """
    raise AttributeError('xx')

@run_in_both(js=False)
def func_fail_exception2():  # This just fails hard
    """
    """
    raise AttributeError('xx')

@run_in_both(py=False)
def func_fail_exception3():  # This just fails hard
    """
    """
    raise AttributeError('xx')


def test_fail_exception():
    with raises(AttributeError):
        func_fail_exception1()
    with raises(AttributeError):
        func_fail_exception2()
    with raises(Exception):  # eval_js turns processerror into Exception
        func_fail_exception3()


if __name__ == '__main__':
    # Run this as a script to
    test_ok1()
    test_ok234()
    test_ok_exception()
    test_fail()
    test_fail_exception()

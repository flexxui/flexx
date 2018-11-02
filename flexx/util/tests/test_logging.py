from flexx.util.testing import run_tests_if_main, raises, skip

import re
from flexx.util.logging import logger, capture_log, set_log_level


def test_debug():

    logger.debug('test')


def test_info():

    logger.info('test')


def test_warning():

    logger.warning('test')


def test_set_log_level():

    with raises(ValueError):
        set_log_level('notaloglevel')

    with raises(TypeError):
        set_log_level([])


def test_capture():

    with capture_log('info') as log:
        logger.warning('AA')
        logger.info('BB')

    msg1 = log[0]
    msg2 = log[1]

    assert 'flexx' in msg1
    assert 'AA' in msg1
    assert '[W ' in msg1

    assert 'flexx' in msg2
    assert 'BB' in msg2
    assert '[I' in msg2


def test_match():

    # Match based on string
    with capture_log('info', 'foo') as log:
        logger.info('AA foo')
        logger.info('BB bar')  # no foo
        logger.debug('CC foo')  # too high level
        logger.info('DD fXo')  # no foo

    assert len(log) == 1
    assert 'AA' in log[0]

    # Match based on regexp
    with capture_log('info', re.compile('f.o')) as log:
        logger.info('AA foo')
        logger.info('BB bar')  # no foo
        logger.debug('CC foo')  # too high level
        logger.info('DD fXo')

    assert len(log) == 2
    assert 'AA' in log[0]
    assert 'DD' in log[1]

    # No match
    with capture_log('info', '') as log:
        logger.info('AA foo')
        logger.info('BB bar')
        logger.debug('CC foo')  # too high level
        logger.info('DD fXo')

    assert len(log) == 3


def test_debug_does_more():

    def caller_func_bla():
        logger.debug('AA foo')
        logger.info('BB bar')

    with capture_log('debug') as log:
        caller_func_bla()

    assert len(log) == 2
    assert 'caller_func_bla' in log[0]
    assert 'caller_func_bla' in log[1]


run_tests_if_main()

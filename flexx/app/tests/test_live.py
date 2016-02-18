""" Test a live app connection.
"""

import os
import sys
from flexx import app, react, webruntime

from flexx.util.testing import run_tests_if_main, raises, skip


ON_TRAVIS = os.getenv('TRAVIS', '') == 'true'
ON_PYPY = '__pypy__' in sys.builtin_module_names


def runner(cls):
    t = app.launch(cls, 'firefox')
    t.test_init()
    app.call_later(5, app.stop)
    app.run()
    if not (ON_TRAVIS and ON_PYPY):  # has intermittent fails on pypy3
        t.test_check()


class BaseTesterApp(app.Model):
    
    
    @react.input
    def input(v):
        return v
    
    @react.input
    def output(v):
        return v
    
    @react.connect('output')
    def _done(self, v):
        self._result = v
        #print('done', v)
        app.stop()
    
    class JS:
        @react.connect('input')
        def _handle_input(self, v):
            #print('handle input', v)
            self.output(v + 1)


class TesterApp1(BaseTesterApp):
    def test_init(self):
        self.input(3)
        self._result = None
    
    def test_check(self):
        assert self._result == 4


class TesterApp2(BaseTesterApp):
    def test_init(self):
        self.input('foo')
        self._result = None
    
    def test_check(self):
        assert self._result == 'foo1'


def test_apps():
    
    # if os.getenv('TRAVIS', '') == 'true':
        # skip('This live test is skipped on Travis for now.')
    if not webruntime.has_firefox():
        skip('This live test needs firefox.')
    
    runner(TesterApp1)
    runner(TesterApp2)


run_tests_if_main()
#if __name__ == '__main__':
#    test_apps()

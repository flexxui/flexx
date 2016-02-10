""" Test a live app connection.
"""

from flexx import app, react

from flexx.util.testing import run_tests_if_main, raises


def runner(cls):
    t = app.launch(cls, 'xul')
    t.test_init()
    app.run()
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
        self.session.close()
    
    class JS:
        @react.connect('input')
        def _handle_input(self, v):
            #print('handling, setting output', v)
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
    runner(TesterApp1)
    runner(TesterApp2)


run_tests_if_main()

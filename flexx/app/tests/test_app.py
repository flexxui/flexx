from flexx.util.testing import run_tests_if_main, raises

from flexx import app, event


class MyPropClass1(app.Model):
    @event.prop
    def foo(self, v=1):
        return v


class MyPropClass2(MyPropClass1):
    def init(self, foo_val=11):
        self.foo = foo_val



def test_launching_with_props():
  
    m = app.launch(MyPropClass1)
    assert m.foo == 1
    m.session.close()
    
    m = app.App(MyPropClass1, foo=3).launch()
    assert m.foo == 3
    m.session.close()


def test_launching_with_init_args():
    
    m = app.launch(MyPropClass2)
    assert m.foo == 11
    m.session.close()
    
    m = app.App(MyPropClass2, 13).launch()
    assert m.foo == 13
    m.session.close()


run_tests_if_main()

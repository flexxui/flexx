from flexx.app._component2 import PyComponent, JsComponent
from flexx.app._component2 import BaseAppComponent, LocalComponent, ProxyComponent
from flexx.event import Component

from flexx import event, app

from flexx.util.testing import run_tests_if_main, raises, skip


class StubSession:
    id = 'y'
    status = 2
    
    def _register_component(self, c, id=None):
        id = id or 'x'
        c._id = id
        c._uid = self.id + '_' + id
    
    def _unregister_component(self, c):
        pass
    
    def send_command(self, *command):
        pass
    
    def keep_alive(self, ob):
        pass


class MyPComponent1(PyComponent):
    
    foo = event.IntProp()
    
    @event.action
    def increase_foo(self):
        self._mutate_foo(self.foo + 1)
    
    @event.reaction('foo')
    def track_foo(self, *events):
        pass
        

class MyJComponent1(JsComponent):
    
    foo = event.IntProp()
    
    @event.action
    def increase_foo(self):
        self._mutate_foo(self.foo + 1)
    
    @event.reaction('foo')
    def track_foo(self, *events):
        pass


class MyPComponent2(MyPComponent1):
    pass


class MyJComponent2(MyJComponent1):
    pass


all_classes = [MyPComponent2, MyJComponent2, MyPComponent2.JS, MyJComponent2.JS,
               MyPComponent1, MyJComponent1, MyPComponent1.JS, MyJComponent1.JS,
               PyComponent, JsComponent, PyComponent.JS, JsComponent.JS,
               LocalComponent, ProxyComponent,
               BaseAppComponent,
               Component]


def test_pycomponent_heritage():
    
    C = MyPComponent2
   
    # Names and repr
    assert C.__name__ == C.JS.__name__
    assert 'PyComponent' in repr(C) and 'PyComponent' in repr(C.JS)
    assert not 'proxy' in repr(C) and 'proxy' in repr(C.JS)
    assert not 'JS' in repr(C) and 'for JS' in repr(C.JS)
    
    mro = [MyPComponent2, MyPComponent1, PyComponent, LocalComponent, BaseAppComponent, Component, object]
    
    # Validate inheritance of py class
    assert C.mro() == mro
    # Also check issubclass()
    for cls in mro:
        assert issubclass(C, cls)
    for cls in all_classes:
        if cls not in mro:
            assert not issubclass(C, cls)
    # Also check isinstance()
    foo = C(flx_session=StubSession())
    for cls in mro:
        assert isinstance(foo, cls)
    for cls in all_classes:
        if cls not in mro:
            assert not isinstance(foo, cls)

    mro = [MyPComponent2.JS, MyPComponent1.JS, PyComponent.JS, ProxyComponent, BaseAppComponent, Component, object]
    
    # Validate inheritance of JS class
    assert C.JS.mro() == mro
    # Also check issubclass()
    for cls in mro:
        assert issubclass(C.JS, cls)
    for cls in all_classes:
        if cls not in mro:
            assert not issubclass(C.JS, cls)


def test_jscomponent_heritage():
    
    session = app.manager.get_default_session()
    if session is None:
        session = app.manager.create_default_session()
    
    C = MyJComponent2
   
    # Names and repr
    assert C.__name__ == C.JS.__name__
    assert 'JsComponent' in repr(C) and 'JsComponent' in repr(C.JS)
    assert 'proxy' in repr(C) and 'proxy' not in repr(C.JS)
    assert not 'JS' in repr(C) and 'for JS' in repr(C.JS)
    
    mro = [MyJComponent2, MyJComponent1, JsComponent, ProxyComponent, BaseAppComponent, Component, object]
     
    # Validate inheritance of py class
    assert C.mro() == mro
    # Also check issubclass()
    for cls in mro:
        assert issubclass(C, cls)
    for cls in all_classes:
        if cls not in mro:
            assert not issubclass(C, cls)
    # Also check isinstance()
    foo = C(flx_session=session)
    for cls in mro:
        assert isinstance(foo, cls)
    for cls in all_classes:
        if cls not in mro:
            assert not isinstance(foo, cls)

    mro = [MyJComponent2.JS, MyJComponent1.JS, JsComponent.JS, LocalComponent, BaseAppComponent, Component, object]
    
    # Validate inheritance of JS class
    assert C.JS.mro() == mro
    # Also check issubclass()
    for cls in mro:
        assert issubclass(C.JS, cls)
    for cls in all_classes:
        if cls not in mro:
            assert not issubclass(C.JS, cls)


def test_properties():
    
    assert MyPComponent2.__properties__ == ['foo']
    assert MyPComponent2.JS.__properties__ == ['foo']
    assert MyJComponent2.__properties__ == ['foo']
    assert MyJComponent2.JS.__properties__ == ['foo']
    
    assert MyPComponent2.__actions__ == ['increase_foo']
    assert MyPComponent2.JS.__actions__ == ['_emit_at_proxy']
    assert MyJComponent2.__actions__ == ['_emit_at_proxy']
    assert MyJComponent2.JS.__actions__ == ['increase_foo']
    
    assert MyPComponent2.__reactions__ == ['track_foo']
    assert MyPComponent2.JS.__reactions__ == []
    assert MyJComponent2.__reactions__ == []
    assert MyJComponent2.JS.__reactions__ == ['track_foo']


def test_cannot_instantiate_without_session():
    
    app.manager.remove_default_session()
    
    with raises(RuntimeError) as err:
        PyComponent()
    assert 'needs a session!' in str(err)
    
    with raises(RuntimeError) as err:
        JsComponent()
    assert 'needs a session!' in str(err)


def test_generated_js():
    m = app.assets.modules['flexx.app._component2']
    js = m.get_js()
    classes = []
    for line in js.splitlines():
        if '._base_class =' in line:
            classes.append(line.split('.')[0])
    assert classes == ['BaseAppComponent',
                       'LocalComponent', 'ProxyComponent', 'StubComponent',
                       'JsComponent', 'PyComponent']
    print(classes)


def test_misc():
    clss = app.get_component_classes()
    assert PyComponent in clss and JsComponent in clss
    assert LocalComponent not in clss and ProxyComponent not in clss
    assert BaseAppComponent not in clss
    
    # Assert that the list is a copy
    clss.remove(PyComponent)
    assert PyComponent in app.get_component_classes()


run_tests_if_main()

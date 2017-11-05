from flexx.app._component2 import PyComponent, JsComponent, LocalComponent, ProxyComponent
from flexx.event import Component

from flexx import event

from flexx.util.testing import run_tests_if_main, raises, skip


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
               Component]


def test_pycomponent_heritage():
    
    C = MyPComponent2
   
    # Names and repr
    assert C.__name__ == C.JS.__name__
    assert 'PyComponent' in repr(C) and 'PyComponent' in repr(C.JS)
    assert not 'proxy' in repr(C) and 'proxy' in repr(C.JS)
    assert not 'JS' in repr(C) and 'for JS' in repr(C.JS)
    
    mro = [MyPComponent2, MyPComponent1, PyComponent, LocalComponent, Component, object]
     
    # Validate inheritance of py class
    assert C.mro() == mro
    # Also check issubclass()
    for cls in mro:
        assert issubclass(C, cls)
    for cls in all_classes:
        if cls not in mro:
            assert not issubclass(C, cls)
    # Also check isinstance()
    foo = C()
    for cls in mro:
        assert isinstance(foo, cls)
    for cls in all_classes:
        if cls not in mro:
            assert not isinstance(foo, cls)

    mro = [MyPComponent2.JS, MyPComponent1.JS, PyComponent.JS, ProxyComponent, Component, object]
    
    # Validate inheritance of JS class
    assert C.JS.mro() == mro
    # Also check issubclass()
    for cls in mro:
        assert issubclass(C.JS, cls)
    for cls in all_classes:
        if cls not in mro:
            assert not issubclass(C.JS, cls)


def test_jscomponent_heritage():
    
    C = MyJComponent2
   
    # Names and repr
    assert C.__name__ == C.JS.__name__
    assert 'JsComponent' in repr(C) and 'JsComponent' in repr(C.JS)
    assert 'proxy' in repr(C) and 'proxy' not in repr(C.JS)
    assert not 'JS' in repr(C) and 'for JS' in repr(C.JS)
    
    mro = [MyJComponent2, MyJComponent1, JsComponent, ProxyComponent, Component, object]
     
    # Validate inheritance of py class
    assert C.mro() == mro
    # Also check issubclass()
    for cls in mro:
        assert issubclass(C, cls)
    for cls in all_classes:
        if cls not in mro:
            assert not issubclass(C, cls)
    # Also check isinstance()
    foo = C()
    for cls in mro:
        assert isinstance(foo, cls)
    for cls in all_classes:
        if cls not in mro:
            assert not isinstance(foo, cls)

    mro = [MyJComponent2.JS, MyJComponent1.JS, JsComponent.JS, LocalComponent, Component, object]
    
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
    assert MyPComponent2.JS.__actions__ == ['increase_foo']
    assert MyJComponent2.__actions__ == ['increase_foo']
    assert MyJComponent2.JS.__actions__ == ['increase_foo']
    
    assert MyPComponent2.__reactions__ == ['track_foo']
    assert MyPComponent2.JS.__reactions__ == []
    assert MyJComponent2.__reactions__ == []
    assert MyJComponent2.JS.__reactions__ == ['track_foo']


foo = MyPComponent2()
print(foo.JS)
run_tests_if_main()
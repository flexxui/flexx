"""
Definition of prop, readonly and event.

"""

import inspect


class Property:
    """ A value that is gettable and settable.
    """
    def __init__(self, func):
        if not callable(func):
            raise ValueError('Property needs a callable')
        self._func = func
        self._name = func.__name__  # updated by HasEvents meta class
        
        # Get whether function is a method
        try:
            self._func_is_method = inspect.getargspec(func)[0][0] in ('self', 'this')
        except (TypeError, IndexError):
            self._func_is_method = False
    
    def __repr__(self):
        cls_name = self.__class__.__name__
        return '<%s for %s at 0x%x>' % (cls_name, self._name, id(self))
    
    def __set__(self, instance, value):
        if isinstance is not None:
            private_name = '_' + self._name + '_prop'
            # Validate value
            self._is_being_set = True
            try:
                if self._func_is_method:
                    value2 = self._func(instance, value)
                else:
                    value2 = self._func(value)
            except Exception as err:
                raise
            
                # if value is undefined:
                #     return  # no need to update
                # for signal in self._downstream_reconnect[:]:  # list may be modified
                #     signal.connect(False)
                # for signal in self._downstream:
                #     signal._set_status(1, self)  # do not set status of *this* signal!
            finally:
                self._is_being_set = False
            # Update value and emit event
            old = getattr(instance, private_name, None)
            setattr(instance, private_name, value2)
            instance.emit(self._name, dict(new_value=value2, old_value=old))
    
    def __delete__(self, instance):
        raise ValueError('Cannot delete property %r.' % self._name)
    
    def __get__(self, instance, owner):
        if instance is None:
            return self
        
        private_name = '_' + self._name + '_prop'
        try:
            return getattr(instance, private_name)
        except AttributeError:
            self.set_default(instance)
    
    def set_default(self, instance):
        private_name = '_' + self._name + '_prop'
        # Trigger default value
        self._is_being_set = True
        try:
            if self._func_is_method:
                value2 = self._func(instance)
            else:
                value2 = self._func()
        except Exception as err:
            raise  # we need a default
        finally:
            self._is_being_set = False
        # Update value and emit event
        old = None
        setattr(instance, private_name, value2)
        instance.emit(self._name, dict(new_value=value2, old_value=old))


class Readonly:
    """ A value that is gettable and only settable by friend-code.
    """
    pass

class Event:
    """ Definition of a type of event. Functions as a placeholder
    for documentation and easy firing of the event.
    """
    pass 



# To apply at a HasEvents class

def prop(func):
    return Property(func)

def readonly(func):
    return Readonly(func)

def event(func):
    return Event(func)





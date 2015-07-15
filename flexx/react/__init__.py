from .reactive import source, input, watch, act, HasSignals, SignalConnectionError
from .reactive import Signal, SourceSignal, InputSignal, WatchSignal, ActSignal


class TestDocs(HasSignals):
    
    @input
    def title(v=''):
        """ The title of the x. """
        return str(v)
    
    @watch('xx')
    def foo(v=''):
        return v
        
    @act('title')
    def show_title(self, v):
        """ Reactor to show the title when it changes. """
        print(v)

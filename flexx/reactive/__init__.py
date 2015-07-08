from .reactive import source, input, signal, react, HasSignals, SignalConnectionError
from .reactive import SourceSignal, InputSignal, Signal, ReactSignal

class TestDocs(HasSignals):
    
    @input
    def title(v=''):
        """ The title of the x. """
        return str(v)
    
    @signal('xx')
    def foo(v=''):
        return v
        
    @react('title')
    def show_title(self, v):
        """ Reactor to show the title when it changes. """
        print(v)

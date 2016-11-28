"""
Module that can dynamically generate stubs.
"""

import sys


class RawJS:
    """ An object to wrap verbatim code to be included in the generated
    JavaScript. This serves a number of purposes:
    
    * Using code in PyScript that is not valid Python syntax, like regular
      expressions or the jQuery object ``$``.
    * Write high performance code that avoids Pythonic features like operator
      overloading.
    * In Flexx's module system it can be used to create a stub variable in
      Python that *does* have a value in JS. This value can imported in other
      modules, leading to a shared value also in JS.
    
    PyScript does not verify the syntax of the code, so write carefully!
    To allow the features in the 3d point, this object has a magic touch:
    the ``__module__`` attribute of an instance refers to the module in which it
    was instantiated, and if it's a global, its defining name can be obtained.
    
    Example:
    
    .. code-block:: py
        
        # Syntax not usable in Py
        myre = VerbatimJS('/ab+c/')
        
        # Code that should only execute on JS
        foo = VerbatimJS('require("some.module")')
        
        # Performance
        def bar(n):
            res = []
            VerbatimJS('''
                for (var i=0; i<n; i++) {
                    if (is_ok_num(i)) {
                        res.push(i);
                    }
                }
            ''')
    
    """
    
    def __init__(self, code, _resolve_defining_module=True):
        if not isinstance(code, str):
            raise TypeError('VerbatimJS requires str input.')
        self._lines = self._str2lines(code)
        
        # Get the globals of the module in which this instance is defined, so
        # that we can set __module__ and later obtain the name by which this 
        # instance is known in that module. We use a trick here to get access
        # to the stack frame while avoiding sys._getframe().
        try:
            raise Exception()
        except Exception as err:
            tb = getattr(err, '__traceback__', None)
            if tb is None:  # Legacy Python 2.x
                import sys
                _, _, tb = sys.exc_info()
            self._globals = tb.tb_frame.f_back.f_globals
            del tb
        self.__module__ = self._globals['__name__']
        self._real_name = None
    
    def __repr__(self):
        if len(self._lines) == 1 and len(self._lines[0]) < 60:
            return '<%s "%s">' % (self.__class__.__name__, self.get_code(0))
        else:
            return '<%s with %i lines>' % (self.__class__.__name__, len(self._lines))
    
    def __str__(self):
        return self.get_code(0)
    
    @classmethod
    def _str2lines(cls, text):
        """ Classmethod to split a text in lines, dedenting each line.
        The first line's indentation will assume the minimal
        indentation.
        """
        lines = text.replace('\r', '').split('\n')
        lines[0] = lines[0].strip()  # firts line is always detented
        if len(lines) > 1:
            # Get minimal indentation
            min_indent = 99999
            for line in lines[1:]:
                if line.strip():  # don't count empty lines
                    min_indent = min(min_indent, len(line) - len(line.lstrip()))
            # Remove indentation
            for i in range(1, len(lines)):
                lines[i] = lines[i][min_indent:].rstrip()
        # Remove empty line only at beginning
        if not lines[0]:
            lines.pop(0)
        return lines
    
    def get_defined_name(self, suggestion=None):
        """ Get the name by which this object is known in the module in which
        it is defined. Only works if it is a global. Returns '' otherwise.
        If a suggestion is given and it is the correct name, this function
        performs faster. The resulting name is cached internally.
        """
        if self._real_name is None:
            self._real_name = ''  # could be defined not in the globals
            if suggestion and self._globals.get(suggestion, None) is self:
                self._real_name = suggestion
            else:
                for name, val in self._globals.items():
                    if val is self:
                        self._real_name = name
                        break
        return self._real_name
    
    def get_code(self, indent=0):
        """ Get the code with the given indentation.
        """
        indent = indent * ' '
        return '\n'.join([indent + line for line in self._lines])


class JSConstant:
    """ Class to represent variables that are used in JS, and are considered
    global or otherwise available in a way that Python cannot know.
    """
    
    def __init__(self, name='jsconstant'):
        self._name = name
    
    def __repr__(self):  # pragma: no cover
        return '<%s %s>' % (self.__class__.__name__, self._name)


class Stubs:
    
    __name__ = __name__
    __file__ = __file__
    JSConstant = JSConstant
    RawJS = RawJS
    
    def __getattr__(self, name):
        if name in ('JSConstant', 'RawJS'):
            return getattr(self, name)
        else:
            return self.JSConstant(name)


# Seems hacky, but is supported: http://stackoverflow.com/a/7668273/2271927
sys.modules[__name__] = Stubs()

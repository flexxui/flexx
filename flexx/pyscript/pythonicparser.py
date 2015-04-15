from .baseparser import BaseParser, JSError, unify


class PythonicParser(BaseParser):
    """ Parser to transcompile Python to JS, allowing more Pythonic
    code, like ``self``, ``print()``, ``len()``, list methods, etc.
    """
    
    NAME_MAP = {'self': 'this', }
    NAME_MAP.update(BaseParser.NAME_MAP)
    
    def function_isinstance(self, node):
        if len(node.args) != 2:
            raise JSError('isinstance expects two arguments.')
        
        ob = unify(self.parse(node.args[0]))
        cls = unify(self.parse(node.args[1]))
        if cls[0] in '"\'':
            cls = cls[1:-1]  # remove quotes
        
        BASIC_TYPES = 'number', 'boolean', 'string', 'function', 'array', 'object', 'null', 'undefined'
        
        MAP = {'(int, float)': 'number', '(float, int)': 'number', 'float': 'number',
               'str': 'string', 'basestring': 'string', 'string_types': 'string',
               'bool': 'boolean',
               'FunctionType': 'function', 'types.FunctionType': 'function',
               'list': 'array', 'tuple': 'array', '(list, tuple)': 'array', '(tuple, list)': 'array',
               'dict': 'object',
              }
        
        cmp = MAP.get(cls, cls)
        
        if cmp.lower() in BASIC_TYPES:
            # Basic type, use Object.prototype.toString 
            # http://stackoverflow.com/questions/11108877
            return ["({}).toString.call(", 
                    ob, 
                    ").match(/\s([a-zA-Z]+)/)[1].toLowerCase() === ", 
                    repr(cmp.lower())
                    ]
        
        else:
            # User defined type, use instanceof
            cmp = unify(cls)
            if cmp[0] == '(':
                raise JSError('isinstance() can only compare to simple types')
            return ob, " instanceof ", cmp
    
    def function_print(self, node):
        # Process keywords
        sep, end = '" "', ''
        for kw in node.keywords:
            if kw.arg == 'sep':
                sep = ''.join(self.parse(kw.value))
            elif kw.arg == 'end':
                end = ''.join(self.parse(kw.value))
            elif kw.arg in ('file', 'flush'):
                raise JSError('print() file and flush args not supported')
            else:
                raise JSError('Invalid argument for print(): %r' % kw.arg)
        
        # Combine args
        args = [unify(self.parse(arg)) for arg in node.args]
        end = (" + %s" % end) if (args and end and end != '\n') else ''
        combiner = ' + %s + ' % sep
        args_concat = combiner.join(args)
        return 'console.log(' + args_concat + end + ')'
    
    def function_len(self, node):
        if len(node.args) == 1:
            return unify(self.parse(node.args[0])), '.length'
        else:
            return None  # don't apply this feature
    
    def method_append(self, node, base):
        if len(node.args) == 1: 
            code = []
            code.append('(%s.append || %s.push).apply(%s, [' % (base, base, base))
            code += self.parse(node.args[0])
            code.append('])')
            return code
    
    def method_remove(self, node, base):
        if len(node.args) == 1: 
            code = []
            remove_func = 'function (x) {%s.splice(%s.indexOf(x), 1);}' % (base, base)
            code.append('(%s.remove || %s).apply(%s, [' % (base, remove_func, base))
            code += self.parse(node.args[0])
            code.append('])')
            return code

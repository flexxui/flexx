from .baseparser import BaseParser, JSError, unify


# todo: self-> this define here?


class PythonicParser(BaseParser):
    """ Parser to transcompile Python to JS, allowing more Pythonic code.
    
    This allows for print(), len(), list methods, etc.
    """
    
    def function_print(self, node, func, args):
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
    
    def function_len(self, node, func, args):
        if len(args) == 1:
            return unify(args[0]), '.length'
    
    def method_append(self, node, func, args):
        base, method = func.rsplit('.', 1)
        code = []
        code.append('(%s.append || %s.push).apply(%s, [' % (base, base, base))
        code += args
        code.append('])')
        return code
    
    def method_remove(self, node, func, args):
        base, method = func.rsplit('.', 1)
        code = []
        remove_func = 'function (x) {%s.splice(%s.indexOf(x), 1);}' % (base, base)
        code.append('(%s.remove || %s).apply(%s, [' % (base, remove_func, base))
        code += args
        code.append('])')
        return code

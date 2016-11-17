"""
Functionality for creating JS modules of various formats, including AMD and UMD.
"""

import re


# Immediately Invoked Function Expression (IIFE)
HIDDEN = """
(function () {

"use strict";

{code}

})();
""".lstrip()


SIMPLE = """
(function (root, factory) {
    root.{save_name} = factory();
}(this, function () {

"use strict";

{code}

return {exports};
}));
""".lstrip()


AMD = """
define("{name}", [{dep_strings}], function ({dep_names}) {

"use strict";

{code}

return {exports};
});
""".lstrip()

AMD_FLEXX = "flexx." + AMD


# https://github.com/umdjs/umd/blob/master/returnExports.js
UMD = """
(function (root, factory) {
    if (typeof define === 'function' && define.amd) {
        // AMD. Register as an anonymous module.
        define("{name}", [{dep_strings}], factory);
    } else if (typeof exports !== 'undefined') {
        // Node or CommonJS
        module.exports = factory({dep_requires});
        if (typeof window === 'undefined') {
            root.{save_name} = module.exports;  // also create global module in Node
        }
    } else {
        // Browser globals (root is window)
        root.{save_name} = factory({dep_fullnames});
    }
}(this, function ({dep_names}) {

"use strict";

{code}

return {exports};
})); 
""".lstrip()


def isidentifier(s):
    # http://stackoverflow.com/questions/2544972/
    if not isinstance(s, str):
        return False
    return re.match(r'^\w+$', s, re.UNICODE) and re.match(r'^[0-9]', s) is None


def create_js_module(name, code, imports, exports, type='umd'):
    """ Wrap the given code in an AMD module.
    
    Note that "use strict" is added to the top of the module body. PyScript
    does not deal with license strings; the caller should do that.
    
    Parameters:
        name (str): the name of the module.
        code (str): the JS code to wrap.
        imports (list): the imports for this module, as string names of the
            dependencies. Optionally, 'as' can  be used to make a dependency
            available under a specific name (e.g. 'foo.js as foo').
        exports (str, list): the result of this module (i.e. what other modules
            get when they import this module. Can be a JS expression or a list
            of names to export.
        type (str): the type of module to export, valid values are
            'hidden', 'simple' (save module on root), 'amd' , 'amd-flexx' and
            'umd' (case insensitive). Default 'umd'.
    """
    
    # Check input args
    if not isinstance(name, str) or not name:
        raise ValueError('create_module() name arg must be a (nonempty) string.')
    if not isinstance(code, str):
        raise ValueError('create_module() code arg must be a string.')
    if not isinstance(imports, (tuple, list)):
        raise ValueError('create_module() imports arg must be a string.')
    if not isinstance(exports, (str, tuple, list)):
        raise ValueError('create_module() exports arg must be a string or list.')
    
    # Process imports
    deps, dep_names = [], []
    for imp in imports:
        if not isinstance(imp, str):
            raise ValueError('Elements in create_module() imports must be str.')
        if ' as ' in imp:
            dep, dep_name = imp.split(' as ', 1)
        else:
            dep = dep_name = imp
        if not isidentifier(dep_name):
            raise ValueError('Import %r is not an identifier, '
                             'have you used "as"?' % dep_name)
        deps.append(dep)
        dep_names.append(dep_name)
    
    # Process exports
    if isinstance(exports, str):
        return_val = exports
    else:  # list
        for exp in exports:
            if not isinstance(exp, str):
                raise ValueError('Elements in create_module() exports must be str.')
        return_val = ', '.join(['%s: %s' % (exp, exp) for exp in exports])
        return_val = '{' + return_val + '}'
    
    # Process type -> select template
    types = {'hidden': HIDDEN, 'simple': SIMPLE,
             'amd': AMD, 'umd': UMD, 'amd-flexx': AMD_FLEXX}
    if not isinstance(type, str):
        raise ValueError('create_js_module() type must be str.')
    if type.lower() not in types:
        raise ValueError('create_js_module() got invalid type %r' % type)
    template = types[type.lower()]
    
    # Derived information needed to populate the module templates
    save_name = lambda n: n.split('/')[-1].split('.')[0].replace('-', '_')
    dep_strings = ['"%s"' % dep for dep in deps]
    dep_fullnames = ['root.' + save_name(dep) for dep in deps]
    dep_requires = ['require("%s")' % dep for dep in deps]
    
    # Fill in the template
    for key, val in [('{name}', name),
                     ('{save_name}', save_name(name)),
                     ('{exports}', return_val),
                     ('{dep_names}', ', '.join(dep_names)),
                     ('{dep_strings}', ', '.join(dep_strings)),
                     ('{dep_fullnames}', ', '.join(dep_fullnames)),
                     ('{dep_requires}', ', '.join(dep_requires)),
                     ('{code}', code),  # last!
                    ]:
        template = template.replace(key, val)
    
    return template

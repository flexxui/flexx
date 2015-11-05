"""
PyScript standard functions.
"""

# Functions not covered by this lib:
# isinstance, issubclass, print, len, max, min, callable, chr, ord

FUNCTIONS = {}
METHODS = {}
FUNCTION_PREFIX = 'py_'
METHOD_PREFIX = '_py_'

def get_partial_std_lib(func_names, method_names, indent=0):
    """ Get the code for the PyScript standard library consisting of
    the given function and method names. The given indent specifies how
    many sets of 4 spaces to prepend.
    """
    lines = []
    for name in sorted(func_names):
        code = FUNCTIONS[name].strip()
        lines.append('var %s%s = %s;' % (FUNCTION_PREFIX, name, code))
    for name in sorted(method_names):
        code = METHODS[name].strip()
        lines.append('Object.prototype.%s%s = %s;' % (METHOD_PREFIX, name, code))
    code = '\n'.join(lines)
    if indent:
        lines = ['    '*indent + line for line in code.splitlines()]
        code = '\n'.join(lines)
    return code

def get_full_std_lib(indent=0):
    """ Get the code for the full PyScript standard library. The given
    indent specifies how many sets of 4 spaces to prepend.
    """
    return get_partial_std_lib(FUNCTIONS.keys(), METHODS.keys(), indent)

## Hardcore functions

FUNCTIONS['hasattr'] = """function (ob, name) {
    return (ob !== undefined) && (ob !== null) && (ob[name] !== undefined);
}"""

FUNCTIONS['getattr'] = """function (ob, name, deflt) {
    var has_attr = ob !== undefined && ob !== null && ob[name] !== undefined;
    if (has_attr) {return ob[name];}
    else if (deflt !== undefined) {return deflt;}
    else {var e = Error(name); e.name='AttributeError'; throw e;}
}"""

FUNCTIONS['setattr'] = """function (ob, name, value) {
    ob[name] = value;
}"""

FUNCTIONS['delattr'] = """function (ob, name) {
    delete ob[name];
}"""

FUNCTIONS['dict'] = """function (x) {
    var t, i, keys, r={};
    if (Array.isArray(x)) {
        for (i=0; i<x.length; i++) {
            t=x[i]; r[t[0]] = t[1];
        }
    } else {
        keys = Object.keys(x);
        for (i=0; i<keys.length; i++) {
            t=keys[i]; r[t] = x[t];
        }
    }
    return r;
}"""

FUNCTIONS['list'] = """function (x) {
    var r=[];
    if (typeof x==="object" && !Array.isArray(x)) {x = Object.keys(x)}
    for (var i=0; i<x.length; i++) {
        r.push(x[i]);
    }
    return r;
}"""

FUNCTIONS['range'] = """function (start, end, step) {
var i, res = [];
    var val = start;
    var n = (end - start) / step;
    for (i=0; i<n; i++) {
        res.push(val);
        val += step;
    }
    return res;
}"""


## Normal functions

FUNCTIONS['pow'] = 'Math.pow'

FUNCTIONS['sum'] = 'function (x) {return x.reduce(function(a, b) {return a + b;});}'

FUNCTIONS['round'] = 'Math.round'

FUNCTIONS['int'] = 'function (x) {return x<0 ? Math.ceil(x): Math.floor(x);}'

FUNCTIONS['float'] = 'Number'

FUNCTIONS['str'] = 'String'

FUNCTIONS['repr'] = 'JSON.stringify'

FUNCTIONS['bool'] = """function (x) {return Boolean(%struthy(x));}
""" % FUNCTION_PREFIX  # note: uses truthy

FUNCTIONS['abs'] = 'Math.abs'

FUNCTIONS['divmod'] = 'function (x, y) {var m = x % y; return [(x-m)/y, m];}'

FUNCTIONS['all'] = """function (x) {
    for (var i=0; i<x.length; i++) {
        if (!%struthy(x[i])){return false}
    } return true;
}""" % FUNCTION_PREFIX  # note: uses truthy

FUNCTIONS['any'] = """function (x) {
    for (var i=0; i<x.length; i++) {
        if (%struthy(x[i])){return true}
    } return false;
}""" % FUNCTION_PREFIX  # note: uses truthy

FUNCTIONS['enumerate'] = """function (iter) {
    var i, res=[];
    if ((typeof iter==="object") && (!Array.isArray(iter))) {iter = Object.keys(iter);}
    for (i=0; i<iter.length; i++) {res.push([i, iter[i]]);}
    return res;
}"""
        
FUNCTIONS['zip'] = """function (iter1, iter2) {
    var i, res=[];
    if ((typeof iter1==="object") && (!Array.isArray(iter1))) {iter1 = Object.keys(iter1);}
    if ((typeof iter2==="object") && (!Array.isArray(iter2))) {iter2 = Object.keys(iter2);}
    var len = Math.min(iter1.length, iter2.length);
    for (i=0; i<len; i++) {res.push([iter1[i], iter2[i]]);}
    return res;
}"""

FUNCTIONS['reversed'] = """function (iter) {
    if ((typeof iter==="object") && (!Array.isArray(iter))) {iter = Object.keys(iter);}
    return iter.slice().reverse();
}"""

FUNCTIONS['sorted'] = """function (iter) {
    if ((typeof iter==="object") && (!Array.isArray(iter))) {iter = Object.keys(iter);}
    return iter.slice().sort();
}"""

FUNCTIONS['filter'] = """function (func, iter) {
    if (typeof func === "undefined" || func === null) {func = function(x) {return x;}}
    if ((typeof iter==="object") && (!Array.isArray(iter))) {iter = Object.keys(iter);}
    return iter.filter(func);
}"""

FUNCTIONS['map'] = """function (func, iter) {
    if (typeof func === "undefined" || func === null) {func = function(x) {return x;}}
    if ((typeof iter==="object") && (!Array.isArray(iter))) {iter = Object.keys(iter);}
    return iter.map(func);
}"""

## Helper functions

FUNCTIONS['truthy'] = """function (v) {
    if (v === null || typeof v !== "object") {return v;}
    else if (v.length !== undefined) {return v.length ? v : false;}
    else if (v.byteLength !== undefined) {return v.byteLength ? v : false;} 
    else {return Object.getOwnPropertyNames(v).length ? v : false;}
}"""

## Methods

# List only

METHODS['append'] = """function (x) {
    if (!Array.isArray(this)) return this.KEY.apply(this, arguments);
    this.push(x);
}"""

METHODS['remove'] = """function (x) {
    if (!Array.isArray(this)) return this.KEY.apply(this, arguments);
    this.splice(this.indexOf(x), 1);
}"""

METHODS['count'] = """function (x) {
    if (!Array.isArray(this)) return this.KEY.apply(this, arguments);
    var count = 0;
    for (var i=0; i<this.length; i++) { 
        if (this[i] == x) {count+=1;}
        //if (%sequals(this[i], x)) {count+=1;}
    } return count;
}""" % FUNCTION_PREFIX  # todo: make this use equals

METHODS['extend'] = """function (x) {
    if (!Array.isArray(this)) return this.KEY.apply(this, arguments);
    this.push.apply(this, x);   
}"""

METHODS['index'] = """function (x, start, stop) {
    if (!Array.isArray(this)) return this.KEY.apply(this, arguments);
    start = (start === undefined) ? 0 : start;
    stop = (stop === undefined) ? this.length : stop;
    start = Math.max(0, ((start < 0) ? this.length + start : start));
    stop = Math.min(this.length, ((stop < 0) ? this.length + stop : stop));
    for (var i=start; i<stop; i++) { 
        if (this[i] == x) {return i;}
        //if (%sequals(this[i], x)) {return i;} // this is why we dont use indexOf
    }
    var e = Error(x); e.name='ValueError'; throw e;
}""" % FUNCTION_PREFIX  # todo: make this use equals

METHODS['insert'] = """function (i, x) {
    if (!Array.isArray(this)) return this.KEY.apply(this, arguments);
    i = (i < 0) ? this.length + i : i;
    this.splice(i, 0, x);
}"""

METHODS['remove'] = """function (x) {
    if (!Array.isArray(this)) return this.KEY.apply(this, arguments);
    for (var i=0; i<this.length; i++) { 
        if (this[i] == x) {this.splice(i, 1); return;}
        //if (%sequals(this[i], x)) {this.splice(i, 1); return;}
    }
    var e = Error(x); e.name='ValueError'; throw e;
}""" % FUNCTION_PREFIX  # todo: make this use equals

METHODS['reverse'] = """function () {this.reverse();}"""

METHODS['sort'] = """function (key, reverse) {
    if (!Array.isArray(this)) return this.KEY.apply(this, arguments);
    var comp = function (a, b) {return key(a) - key(b);};
    comp = Boolean(key) ? comp : undefined; 
    this.sort(comp);
    if (reverse) this.reverse();
}"""

# List and dict

METHODS['clear'] = """function () {
    if (Array.isArray(this)) {
        this.splice(0, this.length);
    } else if (typeof this === 'object') {
    
    } else return this.KEY.apply(this, arguments);
}"""

METHODS['copy'] = """function () {
    if (Array.isArray(this)) {
        return this.slice(0);
    } else if (typeof this === 'object') {
    
    } else return this.KEY.apply(this, arguments);
}"""

METHODS['pop'] = """function (i, d) {
    if (Array.isArray(this)) {
        i = (i === undefined) ? -1 : i;
        i = (i < 0) ? (this.length + i) : i;
        var popped = this.splice(i, 1);
        if (popped.length)  return popped[0];
        var e = Error(i); e.name='IndexError'; throw e;
    } else if (typeof this === 'object') {
    
    } else return this.KEY.apply(this, arguments);
}"""

# Dict only

METHODS['get'] = """function (name, deflt) {
    if (typeof this['KEY'] === 'function') return this.KEY.apply(this, arguments);
    if (this[name] !== undefined) {return this[name];}
    else if (deflt !== undefined) {return deflt;}
    else {return null;}
}"""

METHODS['keys'] = """function () {
    if (typeof this['KEY'] === 'function') return this.KEY.apply(this, arguments);
    return Object.keys(this);
}"""



# String

METHODS['startswith'] = """function (x) {
    if (typeof this['KEY'] === 'function') return this.KEY.apply(this, arguments);
    return this.indexOf(x) == 0;
}"""




## Extra functions / methods

FUNCTIONS['time'] = """function () {return new Date().getTime() / 1000;}"""

FUNCTIONS['perf_counter'] = """function() {
    if (typeof(process) === "undefined"){return performance.now()*1e-3;}
    else {var t = process.hrtime(); return t[0] + t[1]*1e-9;}
}"""  # Work in nodejs and browser



for key in METHODS:
    METHODS[key] = METHODS[key].replace('KEY', key)

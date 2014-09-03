# -*- coding: utf-8 -*-
# Copyright (C) 2014, Almar Klein

""" Reading and saving Zoof Object Notation files. ZON is like
JSON, but a more Pythonic format. Just about 400 lines of code.

Maybe rename this too Zoof Simple Object Notation to be more similar to JSON.
"""

import sys
import re
import time

# From six.py
if sys.version_info[0] >= 3:
    string_types = str,
    integer_types = int,
else:
    string_types = basestring,
    integer_types = (int, long)
float_types = float,


## Dict class 

try:
    from collections import OrderedDict as _dict
except ImportError:
    _dict = dict

class Dict(_dict):
    """ A dict in which the keys can be get and set as if they were
    attributes. Very convenient in combination with autocompletion.
    
    This Dict still behaves as much as possible as a normal dict, and
    keys can be anything that are otherwise valid keys. However, 
    keys that are not valid identifiers or that are names of the dict
    class (such as 'items' and 'copy') cannot be get/set as attributes.
    """
    
    __reserved_names__ = _dict().__dir__()  # Also from OrderedDict
    __pure_names__ = dict().__dir__()
    
    def __getattribute__(self, key):
        try:
            return object.__getattribute__(self, key)
        except AttributeError:
            if key in self:
                return self[key]
            else:
                raise
    
    def __setattr__(self, key, val):
        if key in Dict.__reserved_names__:
            # Either let OrderedDict do its work, or disallow
            if key not in Dict.__pure_names__:
                return _dict.__setattr__(self, key, val)
            else:
                raise AttributeError('Reserved name, this key can only ' +
                                     'be set via ``d[%r] = X``' % key)
        else:
            # if isinstance(val, dict): val = Dict(val) -> no, makes a copy!
            self[key] = val
    
    def __dir__(self):
       names = [k for k in self.keys() if 
                (hasattr(k, 'isidentifier') and k.isidentifier())]
       return Dict.__reserved_names__ + names


## Public functions

def load(filename):
    """ load(filename)
    
    Load a struct from the filesystem using the given filename.
    
    Two modes are supported: text mode stores in a human readable format, 
    and binary mode stores in a more efficient (compressed) binary format.
    
    Parameters
    ----------
    filename : str
        The location in the filesystem of the file to load.
    
    """
    
    # Open file
    text = open(filename, 'rb').read().decode('utf-8')
    reader = ReaderWriter()
    return reader.read(text)


def save(filename, d):
    
    writer = ReaderWriter()
    text = writer.save(d)
    open(filename, 'wb').write(text.encode('utf-8'))
    
    


class ReaderWriter(object):
    
    def read(self, text):
        
        indent = 0
        root = Dict()
        container_stack = [root]
        new_container = None
        
        for i, line in enumerate(text.splitlines()):
            linenr = i + 1
            
            # Strip line
            line2 = line.lstrip()
            
            # Skip comments and empty lines        
            if not line2 or line2[0] == '#':        
                continue 
            
            # Find the indentation
            prev_indent = indent
            indent = len(line) - len(line2)
            if indent == prev_indent:
                pass
            elif indent < prev_indent:
                container_stack.pop(-1)
            elif indent > prev_indent and new_container is not None:
                container_stack.append(new_container)
                new_container = None
            else:
                print('ZON: Ignoring wrong indentation at %i' % linenr)
                indent = prev_indent
            
            # Split name and data using a regular expression
            m = re.search("^\w+? *?=", line2)
            if m:
                i = m.end(0)
                name = line2[:i-1].strip()
                data = line2[i:].lstrip()
            else:
                name = None
                data = line2
           
            # Get value
            value = self.to_object(data, linenr)
            
            # Store the value
            current_container = container_stack[-1]
            if isinstance(current_container, dict):
                if name:
                    current_container[name] = value
                else:
                    print('ZON: unnamed item in dict on line %i' % linenr)
            elif isinstance(current_container, list):
                if name:
                    print('ZON: named item in list on line %i' % linenr)
                else:
                    current_container.append(value)
            else:
                raise RuntimeError('Invalid container %r' % current_container)
            
            # Prepare for next round
            if isinstance(value, (dict, list)):
                new_container = value
        
        return root
    
    
    def save(self, d):
        
        pyver = '%i.%i.%i' % sys.version_info[:3]
        ct = time.asctime()
        lines = []
        lines.append('# -*- coding: utf-8 -*-')
        lines.append('# This Zoof Object Notation (ZON) file was')
        lines.append('# created from Python %s on %s.\n' % (pyver, ct))
        lines.append('')
        lines.extend(self.from_object(None, d, 0))
        
        return '\r\n'.join(lines)
        # todo: pop toplevel dict
    
    def from_object(self, name, value, indent):
        
        # Get object's data
        if value is None:
            data = 'Null'
        elif isinstance(value, integer_types):
            data = self.from_int(value)
        elif isinstance(value, float_types):
            data = self.from_float(value)
        elif isinstance(value, bool):
            data = self.from_int(int(value))
        elif isinstance(value, string_types):
            data = self.from_unicode(value)
        elif isinstance(value, dict):
            data = self.from_dict(value, indent)
        elif isinstance(value, (list, tuple)):
            data = self.from_list(value, indent)
        else:
            # We do not know            
            data = 'Null'
            tmp = repr(value)
            if len(tmp) > 64:
                tmp = tmp[:64] + '...'
            if name is not None:
                print("ZON: %s is unknown object: %s" %  (name, tmp))
            else:
                print("ZON: unknown object: %s" % tmp)
        
        # Finish line (or first line)
        if isinstance(data, string_types):
            data = [data]
        if name:
            data[0] = '%s%s = %s' % (' ' * indent, name, data[0])
        else:
            data[0] = '%s%s' % (' ' * indent, data[0])
        
        return data
    
    def to_object(self, data, linenr):
        
        data = data.lstrip()
        
        # Determine what type of object we're dealing with by reading
        # like a human.
        if not data:
            print('ZON: no value specified at line %i.' % linenr)
        elif data[0] in '-.0123456789':
            return self.to_int_or_float(data, linenr)
        elif data[0] == "'":
            return self.to_unicode(data, linenr)
        elif data.startswith('dict:'):  
            return self.to_dict(data, linenr)
        elif data.startswith('list:') or  data[0] == '[':
            return self.to_list(data, linenr)
        elif data.startswith('Null') or data.startswith('None'):
            return None
        else:
            print("ZON: invalid type on line %i." % linenr)
            return None
    
    def to_int_or_float(self, data, linenr):
        line = data.partition('#')[0]
        try:
            return int(line)
        except ValueError:
            try:
                return float(line)
            except ValueError:
                print("ZON: could not parse number on line %i." % linenr)
                return None
    
    def from_int(self, value):
        return repr(int(value))
    
    def to_int(self, data, linenr):
        # First remove any comments
        data = data.partition('#')[0].strip()
        try:
            return int(data)
        except Exception:
            print("ZON: could not parse integer on line %i." % linenr)
            return None
    
    
    def from_float(self, value):
        # Use general specifier with a very high precision.
        # Any spurious zeros are automatically removed. The precision
        # should be sufficient such that any numbers saved and loaded 
        # back will have the exact same value again. 
        # see e.g. http://bugs.python.org/issue1580
        return repr(float(value))  # '%0.17g' % value
    
    def to_float(self, data, linenr):
        # First remove any comments
        data = data.partition('#')[0].strip()
        try:
            return float(line)
        except Exception:
            print("ZON: could not parse float on line %i." % linenr)
            return None
    
    
    def from_unicode(self, value):
        value = value.replace('\\', '\\\\')
        value = value.replace('\n','\\n')
        value = value.replace('\r','\\r')
        value = value.replace('\x0b', '\\x0b').replace('\x0c', '\\x0c')
        value = value.replace("'", "\\'")
        return "'" + value + "'"
    
    def to_unicode(self, data, linenr):
        # Encode double slashes
        line = data.replace('\\\\','0x07') # temp
        
        # Find string using a regular expression
        m = re.search("'.*?[^\\\\]'|''", line)
        if not m:
            print("ZON: string not ended correctly on line %i." % linenr)
            return None # return not-a-string
        else:
            line = m.group(0)[1:-1]
        
        # Decode stuff        
        line = line.replace('\\n','\n')
        line = line.replace('\\r','\r')
        line = line.replace('\\x0b', '\x0b').replace('\\x0c', '\x0c')
        line = line.replace("\\'","'")
        line = line.replace('0x07','\\')
        return line
    
    
    def from_dict(self, value, indent):
        lines = ["dict:"]
        # Process children        
        for key, val in value.items():
            # Skip all the builtin stuff
            if key.startswith("__"):
                continue
            # Skip methods, or anything else we can call
            if hasattr(val, '__call__'): 
                continue  # Note: py3.x does not have function callable
            # Add!
            lines.extend(self.from_object(key, val, indent+2))
        return lines
    
    def to_dict(self, data, linenr):
        return Dict()
    
    def from_list(self, value, indent):
        # Collect subdata and check whether this is a "small list"
        isSmallList = True
        allowedTypes = integer_types + float_types + string_types
        subItems = []
        for element in value:
            if not isinstance(element, allowedTypes):
                isSmallList = False
            subdata = self.from_object(None, element, 0)  # No indent
            subItems.extend(subdata)
        isSmallList = isSmallList and len(subItems) < 256
        
        # Return data
        if isSmallList:
            return '[%s]' % (', '.join(subItems))
        else:            
            data = ["list:"]
            ind = ' ' * (indent + 2)
            for item in subItems:
                data.append(ind + item)
            return data
    
    def to_list(self, data, linenr):
        value = []
        if data[0] == 'l': # list:
            return list()
        else:
            i0 = 1
            pieces = []
            inString = False
            escapeThis = False
            line = data
            for i in range(1,len(line)):
                if inString:
                    # Detect how to get out
                    if escapeThis:
                        escapeThis = False
                        continue
                    elif line[i] == "\\":
                        escapeThis = True
                    elif line[i] == "'":
                        inString = False
                else:
                    # Detect going in a string, break, or end
                    if line[i] == "'":
                        inString = True
                    elif line[i] == ",":
                        pieces.append(line[i0:i])
                        i0 = i+1
                    elif line[i] == "]":
                        piece = line[i0:i]
                        if piece.strip(): # Do not add if empty
                            pieces.append(piece)
                        break
            else:
                print("ZON: short list not closed right on line %i." % linenr)
            
            # Cut in pieces and process each piece
            value = []
            for piece in pieces:
                v = self.to_object(piece, linenr)
                value.append(v)
            return value

## Tests

if __name__ == '__main__':
    fname = '/home/almar/projects/pylib/pyzolib/ssdf/tests/test1.ssdf'
    d = load(fname)
    save(fname+'.zon', d)

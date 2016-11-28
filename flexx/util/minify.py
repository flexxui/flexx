"""
JavaScript minification tools.
"""

def minify(code, remove_whitespace=False):
    """ Very basic minification of JavaScript code. Will likely support
    more advanced minifcation in the future.
    
    Parameters:
        code (str) : the JavaScript code to minify.
        remove_whitespace (bool) : if True, removes all non-functional
            whitespace. Otherwise remove all trailing whitespace and
            indents using tabs to preserve space. Default False.
    """
    code = remove_comments(code)
    if remove_whitespace:
        code = remove_all_whitespace(code)
    else:
        code = remove_trailing_whitespace(code)
        code = remove_empty_lines(code)
        code = tabbify(code)
    return code

def remove_comments(code):
    chars = ['\n']
    class non_local:
        pass
    non_local._i = -1
    
    def read():
        non_local._i += 1
        if non_local._i < len(code):
            return code[non_local._i]
    def to_end_of_string(c0):
        chars.append(c0)
        while True:
            c = read()
            if not c:
                break
            chars.append(c)
            if c == c0 and chars[-2] != '\\':
                return
    def to_end_of_line():
        while True:
            c = read()
            if c == '\n' or not c:
                break
    def to_end_of_mutiline_comment():
        lastchar = ''
        while True:
            c = read()
            if not c:
                break
            if c == '/' and lastchar == '*':
                return
            lastchar = c
    while True:
        c = read()
        if not c:
            break  # end of code
        elif c == "'" or c == '"':
            to_end_of_string(c)
        elif c == '/' and chars[-1] == '/' and chars[-2] != '\\':
            chars.pop(-1)
            to_end_of_line()
            chars.append('\n')
        elif c == '*' and chars[-1] == '/':
            chars.pop(-1)
            to_end_of_mutiline_comment()
        else:
            chars.append(c)
    chars.pop(0)
    return ''.join(chars)

def remove_all_whitespace(code):
    raise RuntimeError('full whitespace removal for minification is currently broken')
    # todo: this is broken
    code = code.replace('\t', ' ').replace('\r', ' ').replace('\n', ' ')
    space_safe = ' =+-/*&|(){},.><:;'
    chars = ['\n']
    class non_local:
        pass
    non_local._i = -1
    
    def read():
        non_local._i += 1
        if non_local._i < len(code):
            return code[non_local._i]
    while True:
        c = read()
        if not c:
            break  # end of code
        if c in ' ':
            if chars[-1] not in space_safe:
                chars.append(c)
        elif c in space_safe and chars[-1] == ' ':
            chars[-1] = c  # replace last char
        else:
            chars.append(c)
    chars.pop(0)
    return ''.join(chars)
    
def remove_empty_lines(code):
    return '\n'.join([line for line in code.splitlines() if line])

def remove_trailing_whitespace(code):
    return '\n'.join([line.rstrip() for line in code.splitlines()])

def tabbify(code):
    lines = []
    for line in code.splitlines():
        line2 = line.lstrip(' \t')
        indent_str = line[:len(line)-len(line2)]
        for s1, s2 in [('    ', '\t'), ('  ', '\t'), (' ', '')]:
            indent_str = indent_str.replace(s1, s2)
        lines.append(indent_str + line2)
    return '\n'.join(lines)

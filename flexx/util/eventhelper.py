import os


def iter_filenames(dir, ignore):
    for dirpath, dirnames, filenames in os.walk(dir):
        for fname in filenames:
            filename = os.path.join(dirpath, fname)
            if fname.endswith('.py'):
                if fname not in ignore and filename not in ignore:
                    yield os.path.join(dirpath, fname)


def event_helper(dir, ignore=()):
    """ Helper function to convert from the old event system to the new one.
    This function does some basic analysis of the code in the given directory
    and gives locations where properties are used as functions, or where
    handlers seem incorrect. When used inside Pyzo, you can just click on
    the filename to go there and fix it.
    """
    
    props = set()
    
    # Collect properties
    for filename in iter_filenames(dir, ignore):
        text = open(filename, 'rb').read().decode()
        prevline = ''
        for i, line in enumerate(text.splitlines()):
            if prevline.strip().startswith(('@event.prop', '@event.readonly')):
                funcname = line.strip().split('def ')[1].split('(')[0].strip()
                props.add(funcname)
            prevline = line
        
    print('Found props/readonlies:')
    print(props)
    
    # Check correct use of properties
    for filename in iter_filenames(dir, ignore):
        text = open(filename, 'rb').read().decode()
        for i, line in enumerate(text.splitlines()):
            
            for prop in props:
                t = '.%s(' % prop
                if t in line:
                    print('Old use of prop %s in File "%s", line %i' %
                          (prop, filename, i+1))
    
    # Check correct use of handlers
    for filename in iter_filenames(dir, ignore):
        text = open(filename, 'rb').read().decode()
        prevline = ''
        for i, line in enumerate(text.splitlines()):
            if prevline.strip().startswith('@event.connect'):
                if 'def' not in line:
                    continue  # without setting prevline
                if '*events' not in line:
                    funcname = line.strip().split('def ')[1].split('(')[0].strip()
                    print('Suspicious handler %s in File "%s", line %i' %
                          (funcname, filename, i+1))
            prevline = line


if __name__ == '__main__':
    event_helper(r'd:\dev\pylib\arbiter\arbiter\viz', ['transform.py'])

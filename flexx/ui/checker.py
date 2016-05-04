
import os
from flexx import ui

props = []

for dirpath, dirnames, filenames in os.walk(os.path.dirname(ui.__file__)):
    for fname in filenames:
        filename = os.path.join(dirpath, fname)
        if not fname.endswith('.py'):
            continue
        
        text = open(filename, 'rt').read()
        lines = text.splitlines()
        
        for i in range(len(lines)-1):
            line = lines[i]
            
            # Props
            if line.strip().startswith(('@event.prop', '@event.readonly')):
                line1 = lines[i+1]
                name = line1.strip().split(' ')[1].split('(')[0]
                props.append(name)
                if '=' not in line1 or 'self' not in line1:
                    print('Suspecious prop in "%s", line %i, in:\n%s\n%s\n' % 
                          (filename, i+1, line, line1))
            
            if line.strip().startswith('@event.connect'):
                line1 = lines[i+1]
                if '*events' not in line1 or 'self' not in line1:
                    print('Suspecious connect in "%s", line %i, in:\n%s\n%s\n' % 
                          (filename, i+1, line, line1))


for dirpath, dirnames, filenames in os.walk(os.path.dirname(ui.__file__)):
    for fname in filenames:
        filename = os.path.join(dirpath, fname)
        if not fname.endswith('.py'):
            continue
        
        text = open(filename, 'rt').read()
        lines = text.splitlines()
        
        for i in range(len(lines)-1):
            line = lines[i]
            
            if not line.strip().startswith('def'):
                for prop in props:
                    if ('.%s(' % prop) in line:
                        print('Using prop as signal in "%s", line %i, in:\n%s\n' % 
                            (filename, i+1, line))
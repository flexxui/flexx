""" Generate docs for examples.
"""

import os
import json
from types import ModuleType
import flexx
from flexx import ui, app
from urllib.request import urlopen

from uiexample import create_ui_example


THIS_DIR = os.path.dirname(os.path.abspath(__file__))
DOC_DIR = os.path.abspath(os.path.join(THIS_DIR, '..'))
FLEXX_DIR = os.path.dirname(flexx.__file__)

# Get list of (submodule, dirname) tuples
EXAMPLES_DIRS = []
for dname in os.listdir(FLEXX_DIR):
    dirname = os.path.join(FLEXX_DIR, dname, 'examples')
    if os.path.isdir(dirname):
        EXAMPLES_DIRS.append((dname, dirname))

created_files = []

def get_notebook_list():
    url = 'http://api.github.com/repos/zoofio/flexx-notebooks/contents'
    print('downloading %s ... ' % url, end='')
    s = json.loads(urlopen(url, timeout=5.0).read().decode())
    print('done')
    filenames = []
    for file in s:
        if file['name'].endswith('ipynb'):
            filenames.append(file['name'])
    return filenames
    
notebook_list = get_notebook_list()


def main():
    
    # Collect examples
    examples = {}
    for sub, dirname in EXAMPLES_DIRS:
        examples[sub] = {}
        for fname in os.listdir(dirname):
            filename = os.path.join(dirname, fname)
            if os.path.isfile(filename) and fname.endswith('.py') and fname[0] != '_':
                # Create example content
                code = open(filename, 'rt', encoding='utf-8').read()
                text = ':orphan:\n\n'  # avoid toctree warning
                text += '.. _%s:\n\n' % fname
                text += '%s\n%s\n\n' % (fname, '=' * len(fname))
                if sub == 'ui' and code.startswith('# doc-export:'):
                    code = code.split('\n', 1)[1].lstrip()
                    html = create_ui_example(filename, '../..')
                    text +=  '.. raw:: html\n\n    ' + html + '\n\n'
                text += '.. code-block:: py\n    :linenos:\n\n'
                text += '\n    ' + code.replace('\n', '\n    ').rstrip() + '\n'
                
                examples[sub][fname] = text
        if not examples[sub]:
            del examples[sub]
    
        # Write all examples
        output_dir = os.path.join(DOC_DIR, sub, 'examples')
        created_files.append(output_dir)
        if not os.path.isdir(output_dir):
            os.mkdir(output_dir)
        for name in examples[sub]:
            filename = os.path.join(output_dir, name[:-3] + '_src.rst')
            created_files.append(filename)
            open(filename, 'wt', encoding='utf-8').write(examples[sub][name])
    
    # # Create example index page
    # docs = 'Examples'
    # docs += '\n' + '=' * len(docs) + '\n\n'
    # for sub in sorted(examples):
    #     docs += '\n' + sub + ':\n\n'
    #     for name in sorted(examples[sub]):
    #         docs += '* :ref:`%s`\n' % name
    # # Write
    # filename = os.path.join(DOC_DIR, 'examples.rst')
    # created_files.append(filename)
    # open(filename, 'wt', encoding='utf-8').write(docs)
    
    better_names = {'pyscript': 'PyScript'}
    
    # Create example pages per submodule
    for sub, _ in EXAMPLES_DIRS:
        dirname = os.path.join(DOC_DIR, sub)
        if os.path.isdir(dirname):
            docs = better_names.get(sub, sub.capitalize()) + ' examples'
            docs += '\n%s\n\n' % (len(docs) * '=')
            # Include notebooks?
            for fname in notebook_list:
                if fname.endswith('.ipynb') and ('_%s.' % sub) in fname:
                    url = 'https://github.com/zoofIO/flexx-notebooks/blob/master/' + fname
                    docs += '* `%s <%s>`_ (external notebook)\n' % (fname, url)
            # List examples
            for name in sorted(examples[sub]):
                docs += '* :ref:`%s`\n' % name
            if sub == 'ui':
                docs += '\nThere is also an `overview of all ui examples (heavy page) <all_examples.html>`_'
            # Write
            filename = os.path.join(DOC_DIR, sub, 'examples.rst')
            created_files.append(filename)
            open(filename, 'wt', encoding='utf-8').write(docs)
    
    print('  generated %i examples' % sum([len(x) for x in examples.values()]))


def clean():
    while created_files:
        filename = created_files.pop()
        if os.path.isfile(filename):
            os.remove(filename)
        elif os.path.isdir(filename) and not os.listdir(filename):
            os.rmdir(filename)

""" Generate docs for examples.
"""

import os
import json
from types import ModuleType
from flexx import ui, app
from urllib.request import urlopen


THIS_DIR = os.path.dirname(os.path.abspath(__file__))
DOC_DIR = os.path.abspath(os.path.join(THIS_DIR, '..'))
EXAMPLES_DIR = os.path.abspath(os.path.join(DOC_DIR, '..', 'examples'))
OUTPUT_DIR = os.path.join(DOC_DIR, 'examples')

created_files = []

def get_notebook_list():
    url = 'https://api.github.com/repos/zoofio/flexx-notebooks/contents'
    s = json.loads(urlopen(url, timeout=5.0).read().decode())
    filenames = []
    for file in s:
        if file['name'].endswith('ipynb'):
            filenames.append(file['name'])
    return filenames
    
notebook_list = get_notebook_list()


def main():
    
    # Collect examples
    examples = {}
    for sub in os.listdir(EXAMPLES_DIR):
        dirname = os.path.join(EXAMPLES_DIR, sub)
        if os.path.isdir(dirname):
            examples[sub] = {}
            for fname in os.listdir(dirname):
                filename = os.path.join(dirname, fname)
                if os.path.isfile(filename) and fname.endswith('.py'):
                    # Create example content
                    code = open(filename, 'rt', encoding='utf-8').read()
                    text = ':orphan:\n\n'  # avoid toctree warning
                    text += '.. _%s:\n\n' % fname
                    text += '%s\n%s\n\n' % (fname, '=' * len(fname))
                    text += '.. code-block:: py\n    :linenos:\n\n'
                    text += '\n    ' + code.replace('\n', '\n    ').rstrip() + '\n'
                    examples[sub][fname] = text
            if not examples[sub]:
                del examples[sub]
    
    # Write all examples
    created_files.append(OUTPUT_DIR)
    if not os.path.isdir(OUTPUT_DIR):
        os.mkdir(OUTPUT_DIR)
    for sub in list(examples.keys()):
        dirname = os.path.join(OUTPUT_DIR, sub)
        created_files.append(dirname)
        if not os.path.isdir(dirname):
            os.mkdir(dirname)
        for name in examples[sub]:
            filename = os.path.join(dirname, name + '.rst')
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
    for sub in examples:
        dirname = os.path.join(DOC_DIR, sub)
        if os.path.isdir(dirname):
            docs = better_names.get(sub, sub.capitalize()) + ' examples'
            docs += '\n%s\n\n' % (len(docs) * '=')
            # Include notebooks?
            for fname in notebook_list:
                if fname.endswith('.ipynb') and ('_%s.' % sub) in fname:
                    url = 'http://github.com/zoofIO/flexx-notebooks/blob/master/' + fname
                    docs += '* `%s <%s>`_ (external notebook)\n' % (fname, url)
            # List examples
            for name in sorted(examples[sub]):
                docs += '* :ref:`%s`\n' % name
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
    
    # Bit of a hack; we do some work for the uiexamples directive here ...
    from flexx import app
    HTML_DIR = os.path.abspath(os.path.join(THIS_DIR, '..', '_build', 'html'))
    app.assets.export(os.path.join(HTML_DIR, 'ui', 'examples'))

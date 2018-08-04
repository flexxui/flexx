""" Generate docs for examples.
"""

import os
import json
import shutil
from types import ModuleType
import flexx
from flexx import ui, app
from urllib.request import urlopen, Request

from uiexample import create_ui_example


THIS_DIR = os.path.dirname(os.path.abspath(__file__))
DOC_DIR = os.path.abspath(os.path.join(THIS_DIR, '..'))
EXAMPLES_DIR = os.path.join(os.path.dirname(DOC_DIR), 'flexxamples')

# Get list of (submodule, dirname) tuples
EXAMPLES_DIRS = []
for dname in os.listdir(EXAMPLES_DIR):
    dirname = os.path.join(EXAMPLES_DIR, dname)
    if os.path.isfile(os.path.join(dirname, '__init__.py')):
        EXAMPLES_DIRS.append((dname, dirname))

created_files = []


# NOTE: not used anymore, but keep in case we want to automate again
def get_notebook_list():
    url = 'https://api.github.com/repos/flexxui/flexx-notebooks/contents'
    print('downloading %s ... ' % url, end='')
    # https://github.com/travis-ci/travis-ci/issues/5649
    req = Request(url, headers={'User-Agent': 'flexx/%s' % flexx.__version__})
    s = json.loads(urlopen(req, timeout=5.0).read().decode())
    print('done')
    filenames = []
    for file in s:
        if file['name'].endswith('ipynb'):
            filenames.append(file['name'])
    return filenames


def main():
    
    # Get output dir and ensure that it is empty
    # Upon App.export() we do not overwrite, because all examples share
    # several common assets. This safes a lot of time.
    output_dir = os.path.join(DOC_DIR, 'examples')
    if os.path.isdir(output_dir):
        shutil.rmtree(output_dir)
    os.mkdir(output_dir)
    
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
                if code.startswith('# doc-export:'):
                    code = code.split('\n', 1)[1].lstrip()
                    html = create_ui_example(filename, '..', source=filename)
                    text +=  '.. raw:: html\n\n    ' + html + '\n\n'
                text += '.. code-block:: py\n    :linenos:\n\n'
                text += '\n    ' + code.replace('\n', '\n    ').rstrip() + '\n'
                
                examples[sub][fname] = text
        if not examples[sub]:
            del examples[sub]
    
        # Write source for all examples
        for name in examples[sub]:
            filename = os.path.join(output_dir, name[:-3] + '_src.rst')
            created_files.append(filename)
            open(filename, 'wt', encoding='utf-8').write(examples[sub][name])
    
    # Create example page
    docs = 'Examples'
    docs += '\n%s\n\n' % (len(docs) * '=')
    
    for sub, _ in EXAMPLES_DIRS:
        section = sub.capitalize()
        docs += '\n%s\n%s\n\n' % (section, len(section) * '-')
        for name in sorted(examples[sub]):
            docs += '* :ref:`%s`\n' % name
        
    filename = os.path.join(DOC_DIR, 'examples', 'index.rst')
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

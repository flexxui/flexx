"""
Small sphinx extension to show a UI example + result
"""

import os
import sys
import shutil
import hashlib
import warnings
import subprocess
import importlib.util

from docutils.parsers.rst import Directive
from docutils import nodes

from flexx import app

THIS_DIR = os.path.abspath(os.path.dirname(__file__))
ROOT_DIR = os.path.dirname(os.path.dirname(THIS_DIR))
HTML_DIR = os.path.abspath(os.path.join(THIS_DIR, '..', '_build', 'html'))

SIMPLE_CODE_T1 = """
from flexx import app, ui

class App(ui.Widget):

    def init(self):
        """  # mind the indentation

SIMPLE_CODE_T2 = """
from flexx import flx

class App(flx.Widget):

    def init(self):
        """  # mind the indentation

all_examples = []


class uiexample(nodes.raw): pass


def create_ui_example(filename, to_root, height=300, source=None):
    """ Given a filename, export the containing app to HTML, return
    generated HTML. Needs to be done via filename, not direct code, so
    that PScript can obtain source.
    """
    code = open(filename, 'rb').read().decode()
    fname = os.path.split(filename)[1]
    filename_parts = 'examples', fname[:-3] + '.html'
    filename_abs = os.path.join(HTML_DIR, *filename_parts)
    filename_rel = to_root + '/' + '/'.join(filename_parts)
    
    # Import - mod_name must be unique, because JS modules match Py modules
    try:
        mod_name = "app_" + fname[:-3]
        if sys.version_info >= (3, 5):
            spec = importlib.util.spec_from_file_location(mod_name, filename)
            m = importlib.util.module_from_spec(spec)
            sys.modules[mod_name] = m  # Flexx needs to be able to access the module
            spec.loader.exec_module(m)
        else:  # http://stackoverflow.com/a/67692/2271927
            from importlib.machinery import SourceFileLoader
            m = SourceFileLoader(mod_name, filename).load_module()
            sys.modules[mod_name] = m
    except Exception as err:
        err_text = str(err)
        msg = 'Example not generated. <pre>%s</pre>' % err_text
        if os.environ.get('READTHEDOCS', False):
            msg = 'This example is not build on read-the-docs. <pre>%s</pre>' % err_text
        open(filename_abs, 'wt', encoding='utf-8').write(msg)
        warnings.warn('Could not import ui example in %s: %s' % (source or filename, err_text))
        return get_html(filename_rel, 60)
    
    # Get class name
    line1 = code.splitlines()[0]
    class_name = None
    if 'class App(' in code:
        class_name = 'App'
    elif 'class MyApp' in code:
        class_name = 'MyApp'
    elif 'class Example' in code:
        class_name = 'Example'
    elif line1.startswith('# doc-export:'):
        class_name = line1.split(':', 1)[1].strip()
    #
    if class_name:
        assert class_name.isidentifier()
    else:
        msg = 'Could not determine app widget class in:<pre>%s</pre>' % code
        warnings.warn(msg)
        open(filename_abs, 'wt', encoding='utf-8').write(msg)
        return get_html(filename_rel, height)
    
    # Export
    try:
        app.export(m.__dict__[class_name], filename_abs, link=2, overwrite=False)
    except Exception as err:
        err_text = str(err)
        msg = 'Example not generated. <pre>%s</pre>' % err_text
        open(filename_abs, 'wt', encoding='utf-8').write(msg.replace('\\n', '<br />'))
        print('==========\n%s\n==========' % code)
        print('ERROR: Could not export ui example: %s in %s\nSee code above.' % (err_text, fname))
        raise err
    
    all_examples.append((class_name, mod_name, filename_parts[-1]))
    return get_html(filename_rel, height)


def get_html(filename_rel, height):
    """ Get the html to embed the given page into another page using an iframe.
    """
    # Styles
    astyle = 'font-size:small; float:right;'
    dstyle = ('width: 500px; height: %ipx; align: center; resize:both; overflow: hidden; '
              'box-shadow: 5px 5px 5px #777; padding: 4px;')
    istyle = 'width: 100%; height: 100%; border: 2px solid #094;'
    
    # Show app in iframe, wrapped in a resizable div
    html = ''
    html += "<a target='new' href='%s' style='%s'>open in new tab</a>" % (filename_rel, astyle)
    html += "<div style='%s'>" % dstyle % height
    html += "<iframe src='%s' style='%s'>iframe not supported</iframe>" % (filename_rel, istyle)
    html += "</div>"
    
    return html


def visit_uiexample_html(self, node):
    global should_export_flexx_deps
    
    # Fix for rtd
    if not hasattr(node, 'code'):
        return
    
    # Get code
    code = ori_code = node.code.strip() + '\n'
    
    # Is this a simple example?
    if 'import' not in code:
        if 'flx.' in code:
            code = SIMPLE_CODE_T2 + '\n        '.join([line for line in code.splitlines()])
        else:
            code = SIMPLE_CODE_T1 + '\n        '.join([line for line in code.splitlines()])
    
    # Get id and filename
    this_id = hashlib.md5(code.encode('utf-8')).hexdigest()
    fname = 'example%s.html' % this_id
    filename_py = os.path.join(HTML_DIR, 'examples', 'example%s.py' % this_id)
    
    # Write Python file
    with open(filename_py, 'wb') as f:
        f.write(code.encode())
    
    # Get html file
    html = create_ui_example(filename_py, '..', node.height, source=node.source)
    self.body.append(html + '<br />')


def depart_uiexample_html(self, node):
    pass

class UIExampleDirective(Directive):
        has_content = True
        def run(self):
            # Get code and extact height
            code = '\n'.join(self.content)
            try:
                height = int(self.content[0])
            except Exception:
                height = 300
            else:
                code = code.split('\n', 1)[1].strip()
            
            # Code block
            literal = nodes.literal_block(code, code)
            literal['language'] = 'python'
            literal['linenos'] = False
            
            # iframe
            iframe = uiexample('')
            iframe.code = code
            iframe.height = height
            
            return[literal, iframe]


def setup(Sphynx):
    
    Sphynx.add_node(uiexample, html=(visit_uiexample_html, depart_uiexample_html))
    Sphynx.add_directive('uiexample', UIExampleDirective)
    Sphynx.connect('build-finished', finish)
    
    examples_dir = os.path.join(HTML_DIR, 'examples')
    if os.path.isdir(examples_dir):
        shutil.rmtree(examples_dir)  # because we export with overwrite==False
    os.makedirs(examples_dir)


def finish(Sphynx, *args):
    
    # Write overview page that contains *all* examples
    parts = []
    for class_name, mod_name, fname in all_examples:
        parts.append('<br /><h3>%s in %s</h3>' % (class_name, mod_name))
        parts.append(get_html('examples/' + fname, 300))
    parts.insert(0, '<!DOCTYPE html><html><body>This page may take a while to load ... <br />')
    parts.append('</body></html>')
    code = '\n'.join(parts)
    with open(os.path.join(HTML_DIR, 'examples', 'all_examples.html'), 'wb') as file:
        file.write(code.encode())

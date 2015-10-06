"""
Small sphinx extension to show a UI example + result
"""

import os
import sys
import hashlib
import warnings
import subprocess

from sphinx.util.compat import Directive
from docutils import nodes

THIS_DIR = os.path.abspath(os.path.dirname(__file__))
ROOT_DIR = os.path.dirname(os.path.dirname(THIS_DIR))
HTML_DIR = os.path.abspath(os.path.join(THIS_DIR, '..', '_build', 'html'))

if not os.path.isdir(HTML_DIR + '/ui'):
    os.mkdir(HTML_DIR + '/ui')
    
if not os.path.isdir(HTML_DIR + '/ui/examples'):
    os.mkdir(HTML_DIR + '/ui/examples')

# Make us find the modules that we write
sys.path.insert(0, HTML_DIR + '/ui/examples')

SIMPLE_CODE_T = """
from flexx import app, ui

class App(ui.Widget):

    def init(self):
        """  # mind the indentation


class uiexample(nodes.raw): pass

def visit_uiexample_html(self, node):
    global should_export_flexx_deps
    
    # Fix for rtd
    if not hasattr(node, 'code'):
        return
    
    # Get code
    code = ori_code = node.code.strip() + '\n'
    ori_code = '\n'.join([' '*8 + x for x in ori_code.splitlines()])  # for reporting
    
    # Is this a simple example?
    if 'import' not in code:
        code = SIMPLE_CODE_T + '\n        '.join([line for line in code.splitlines()])
    
    # Get id and filename
    this_id = hashlib.md5(code.encode('utf-8')).hexdigest()
    fname = 'example%s.html' % this_id
    filename_html = os.path.join(HTML_DIR, 'ui', 'examples', fname)
    filename_py = os.path.join(HTML_DIR, 'ui', 'examples', 'example%s.py' % this_id)
    
    # Compose code
    code += '\n\n'
    if 'class MyApp' in code:
        code += 'App = MyApp\n'
    elif 'class Example' in code:
        code += 'App = Example\n'
    if not 'app' in code:
        code += 'from flexx import app\n'
    code += 'app.export(App, %r, False)\n' % filename_html
    
    # Write filename so Python can find the source
    open(filename_py, 'wt', encoding='utf-8').write(code)
    
    try:
        __import__('example%s' % this_id)  # import to exec
    except ImportError as err:
        err_text = str(err)
        msg = 'Example not generated. <pre>%s</pre>' % err_text
        if os.environ.get('READTHEDOCS', False):
            node.height = 60
            msg = 'This example is not build on read-the-docs. <pre>%s</pre>' % err_text
        open(filename_html, 'wt', encoding='utf-8').write(msg)
        warnings.warn('Ui example dependency not met: %s' % err_text)
    except Exception as err:
        err_text = str(err)
        msg = 'Example not generated. <pre>%s</pre>' % err_text
        open(filename_html, 'wt', encoding='utf-8').write(msg.replace('\\n', '<br />'))
        raise RuntimeError('Could not create ui example: %s\n%s' % (err_text, ori_code) )
        #print('Could not create ui example: %s\n%s' % (err_text, ori_code) )
    
    rel_path = '../ui/examples/' + fname
    
    # Styles
    astyle = 'font-size:small; float:right;'
    dstyle = 'width: 500px; height: %ipx; align: center; resize:both; overflow: hidden; box-shadow: 5px 5px 5px #777;'
    istyle = 'width: 100%; height: 100%; border: 2px solid #094;'
    
    # Show app in iframe, wrapped in a resizable div
    self.body.append("<a target='new' href='%s' style='%s'>open in new tab</a>" % (rel_path, astyle))
    self.body.append("<div style='%s'>" % dstyle % node.height)
    self.body.append("<iframe src='%s' style='%s'>iframe not supported</iframe>" % (rel_path, istyle))
    self.body.append("</div>")
    self.body.append("<br />")


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
    
    #Sphynx.add_javascript('js-image-slider.js')
    #Sphynx.add_stylesheet('js-image-slider.css')
    
    Sphynx.add_node(uiexample, html=(visit_uiexample_html, depart_uiexample_html))
    Sphynx.add_directive('uiexample', UIExampleDirective)

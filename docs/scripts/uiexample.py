"""
Small sphinx extension to show a UI example + result
"""

import os
import hashlib
import warnings

from sphinx.util.compat import Directive
from docutils import nodes

THIS_DIR = os.path.abspath(os.path.dirname(__file__))
HTML_DIR = os.path.abspath(os.path.join(THIS_DIR, '..', '_build', 'html'))

if not os.path.isdir(HTML_DIR + '/ui'):
    os.mkdir(HTML_DIR + '/ui')
    
if not os.path.isdir(HTML_DIR + '/ui/examples'):
    os.mkdir(HTML_DIR + '/ui/examples')


class uiexample(nodes.raw): pass

def visit_uiexample_html(self, node):
    
    # Get code
    code = node.code.strip() + '\n'
    
    # Get id and filename
    this_id = hashlib.md5(code.encode('utf-8')).hexdigest()
    fname = 'example%s.html' % this_id
    
    # Execute code to create App class
    NS = {}
    try:
        exec(node.code, NS, NS)
    except Exception as err:
        warnings.warn('ERROR:' + str(err))
    # todo: raise once we've got it fixed...
    
    # Export app to html file
    for appname in ('App', 'MyApp'):
        if appname in NS:
            try:
                NS[appname].export(os.path.join(HTML_DIR, 'ui', 'examples', fname))
            except Exception as err:
                warnings.warn('ERROR:' + str(err))
            break
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

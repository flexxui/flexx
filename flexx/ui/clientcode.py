"""
Implements a single class that can provide the client code (HTML/JS/CSS)
in diffent ways. This streamlines the inclusion in Jupyter and our
export mechanism.
"""

import os
from collections import OrderedDict

THIS_DIR = os.path.abspath(os.path.dirname(__file__))
HTML_DIR = os.path.join(os.path.dirname(THIS_DIR), 'html')

INDEX = """
<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>Zoof UI</title>

<style>
CSS-HERE
</style>

<script>
JS-HERE
</script>

</head>

<body id='body'>
    
    <div id="log" style="display: none;"> LOG:<br><br></div>

</body>
</html>
"""

JS_BOOTSTRAP = """
// Init zoof namespace
window.zoof = window.zoof || {};
zoof.ws = null;
zoof.is_full_page = true;
zoof.ws_url = "ws://" + location.hostname + ':' + location.port + "/" + location.pathname + "/ws";
zoof.isExported = false;
"""

CSS_BOOTSTRAP = """
"""


class ClientCode(object):
    """ Collect code that the client needs and provide a few ways to
    get the code to the client.
    """
    
    def __init__(self):
        self._files = OrderedDict()
        self._cache = {}
        self._mirrored_js = None
        self._mirrored_css = None
        
        self._in_nb = False
        self._collected = False
    
    def collect(self):
        if self._collected:
            return
        self._collected = True
        
        # Determine JS files
        for fname in ['serialize.js', 'main.js', 'layouts.js',
                     ]:# 'phosphor-core.min.js', 'phosphor-ui.min.js']:
            if fname.startswith('phosphor'):
                self._files[fname] = os.path.join(HTML_DIR, 'phosphor', fname)
            else:
                self._files[fname] = os.path.join(HTML_DIR, fname)
        
        # Determine CSS files
        for fname in ['main.css', 'layouts.css', ]:#'phosphor-ui.min.css']:
            if fname.startswith('phosphor'):
                self._files[fname] = os.path.join(HTML_DIR, 'phosphor', fname)
            else:
                self._files[fname] = os.path.join(HTML_DIR, fname)
        
        # Collect JS from mirrored classes
        from .mirrored import get_mirrored_classes
        self._mirrored_js, self._mirrored_css = [], []
        for cls in get_mirrored_classes():
            self._mirrored_js.append(cls.get_js())
            self._mirrored_css.append(cls.get_css())
    
    def load(self, fname):
        """ Get the source of the given file as a string.
        """
        self.collect()
        if fname not in self._files:
            raise IOError('Invalid source file')
        elif fname in self._cache:
            return self._cache[fname]
        else:
            filename = self._files[fname]
            src = open(filename, 'rt').read()
            #self._cache[fname] = src  # caching disabled for easer dev
            return src
    
    def get_js(self):
        """ Get all JavaScript as a single string.
        """
        self.collect()
        parts = []
        parts.append(JS_BOOTSTRAP)
        # Files
        for fname in self._files:
            if fname.endswith('.js'):
                parts.append('/* ===== %s ===== */' % fname)
                parts.append(self.load(fname))
        # Mirrored code
        parts.append('// Python -> JS code')
        for src in self._mirrored_js:
            parts.append(src)
        return '\n\n'.join(parts)
    
    def get_css(self):
        """ Get all CSS packed in a single <style> tag.
        """
        self.collect()
        parts = []
        parts.append(CSS_BOOTSTRAP)
        for fname in self._files:
            if fname.endswith('.css'):
                parts.append('/* ===== %s ===== */' % fname)
                parts.append(self.load(fname))
        # Mirrored code
        parts.append('/* ===== Python-defined CSS ===== */')
        for src in self._mirrored_css:
            parts.append(src)
        return '\n\n'.join(parts)
    
    def get_page(self):
        """ Get the string for a single HTML page that can show a Flexx app.
        """
        src = INDEX
        src = src.replace('CSS-HERE', self.get_css())
        src = src.replace('JS-HERE', self.get_js())
        return src
    
    def get_page_light(self):
        """ Get a page that relies on external flexx.js and flexx.css.
        """
        raise NotImplementedError()
    
    def build(self, dirname):
        """ Create the flexx js library and css file. Place in the given dir.
        """
        assert os.path.isdir(dirname)
        with open(os.path.join(dirname, 'flexx.js')) as f:
            f.write(self.get_js())
        with open(os.path.join(dirname, 'flexx.css')) as f:
            f.write(self.get_css())
    
    def export(self, filename):
        """ Export the current app to a single HTML page.
        """
        # todo: needs commands
        with open(filename, 'wt') as f:
            f.write(self.get_page())
    
    
    def export_light(self, filename):
        """ Get a page that relies on external flexx.js and flexx.css.
        """
        raise NotImplementedError()
    
    
    
clientCode = ClientCode()
# todo: minification

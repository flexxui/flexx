"""

Image example:

.. UIExample:: 100
    
    from flexx import ui, event
    
    class Example(ui.Widget):
        
        def init(self):
            with ui.HBox():
                self.stretch = ui.CheckBox(text='Stretch')
                with ui.SplitPanel(flex=1):
                    self.im1 = ui.ImageWidget(source='http://github.com/fluidicon.png')
                    self.im2 = ui.ImageWidget(source='http://github.com/fluidicon.png')
        
        class JS:
            
            @event.connect('stretch.checked')
            def make_stretched(self, *events):
                self.im1.stretch = self.im2.stretch = self.stretch.checked


Video example:

.. UIExample:: 100
    
    from flexx import ui
    
    class Example(ui.Widget):
        
        def init(self):
            with ui.HBox():
                with ui.SplitPanel(flex=1):
                    url = 'http://www.w3schools.com/tags/mov_bbb.mp4'
                    self.vid1 = ui.VideoWidget(source=url)
                    self.vid2 = ui.YoutubeWidget(source='dhRUe-gz690')
"""

from ... import event
from ...pyscript import window
from . import Widget


class ImageWidget(Widget):
    """ Display an image using a url.
    """
    
    _sequence = 0
    
    class Both:
        
        @event.prop
        def source(self, v=''):
            """ The source of the image, This can be anything that an HTML
            img element supports.
            """
            return str(v)
        
        @event.prop
        def stretch(self, v=False):
            """ Whether the image should stretch to fill all available
            space, or maintain its aspect ratio (default).
            """
            return bool(v)
    
    class JS:
        
        def _init_phosphor_and_node(self):
            self.phosphor = self._create_phosphor_widget('div')
            self.node = window.document.createElement('img')
            self.phosphor.node.appendChild(self.node)
        
        @event.connect('size', 'stretch')
        def __resize_image(self, *events):
            size = self.size
            if self.stretch:
                self.node.style.maxWidth = None
                self.node.style.maxHeight = None
                self.node.style.width = size[0] + 'px'
                self.node.style.height = size[1] + 'px'
            else:
                self.node.style.maxWidth = size[0] + 'px'
                self.node.style.maxHeight = size[1] + 'px'
                self.node.style.width = None
                self.node.style.height = None
        
        @event.connect('source')
        def __source_changed(self, *events):
            self.node.src = self.source


class VideoWidget(Widget):
    """ A widget to display a video from a url.
    """
    
    class Both:
            
        @event.prop
        def source(self, v=''):
            """ The source of the video. This must be a url of a resource
            on the web.
            """
            return str(v)
    
    class JS:
        
        def _init_phosphor_and_node(self):
            self.phosphor = self._create_phosphor_widget('video')
            self.node = self.phosphor.node
            self.node.controls = 'controls'
            self.node.innerHTML = 'Your browser does not support HTML5 video.'
            
            self.src_node = window.document.createElement('source')
            self.src_node.type = 'video/mp4'
            self.node.appendChild(self.src_node)
        
        @event.connect('source')
        def __source_changed(self, *events):
            self.src_node.src = self.source
            self.node.load()


class YoutubeWidget(Widget):
    """ A widget to display a Youtube video.
    """
    
    class Both:
            
        @event.prop
        def source(self, v='oHg5SJYRHA0'):
            """ The source of the video represented as the Youtube id.
            """
            return str(v)
    
    class JS:
        
        def _init_phosphor_and_node(self):
            self.phosphor = self._create_phosphor_widget('div')
            
            self.inode = window.document.createElement('iframe')
            self.phosphor.node.appendChild(self.inode)
            self.inode.style.margin = '5px'
            
            # We use an overlay to capture mouse events so that we can
            # still use this in a SlitterPanel. We turn the overlay
            # on when the mouse enters the widget (thats why we need a margin)
            # and off when there is a mouse move that is not a drag.
            
            self.overlay_node = window.document.createElement('div')
            self.phosphor.node.appendChild(self.overlay_node)
            self.overlay_node.style.position = 'absolute'
            self.overlay_node.style.opacity = '0.0'
            self.overlay_node.style.top = '0px'
            self.overlay_node.style.left = '0px'
            
            self.node = self.overlay_node
            self.phosphor.node.addEventListener('mouseenter', self._show_overlay, False)
        
        @event.connect('size')
        def _update_canvas_size(self, *events):
            size = self.size
            if size[0] or size[1]:
                self.inode.style.width = size[0] + 'px'
                self.inode.style.height = size[1] + 'px'
                self.overlay_node.style.width = size[0] + 'px'
                self.overlay_node.style.height = size[1] + 'px'
                
        @event.connect('source')
        def __source_changed(self, *events):
            base_url = 'http://www.youtube.com/embed/'
            self.inode.src = base_url + self.source + '?autoplay=0'
        
        @event.connect('mouse_move', 'mouse_down')
        def _hide_overlay(self, *events):
            ev = events[-1]
            if not ev.buttons:
                self.overlay_node.style.width = '0px'
        
        def _show_overlay(self):
            self.overlay_node.style.width = self.size[0] + 'px'


# todo: SVG? Icon?

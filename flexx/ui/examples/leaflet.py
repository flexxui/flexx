# doc-export: LeafletExample
"""
This example demonstrates the use of Leaflet to display a slippy map.
"""


import os
from urllib.request import urlopen, Request
import re
import base64
import mimetypes

import flexx
from flexx import event, app
from flexx.pyscript.stubs import window, L
from flexx.ui import Widget


_leaflet_url = 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/'
_leaflet_version = '1.0.3'
_leaflet_icons = [
    'marker-icon.png',
    'marker-icon-2x.png',
    'marker-shadow.png',
]


if 'LEAFLET_DIR' in os.environ:
    _base_url = 'file://%s' % os.environ['LEAFLET_DIR']
else:
    _base_url = '%s/%s' % (_leaflet_url, _leaflet_version)
mimetypes.init()


def _get_code(item):
    """ Get a text item from _base_url
    """
    url = '%s/%s' % (_base_url, item)
    req = Request(url, headers={'User-Agent': 'flexx/%s' % flexx.__version__})
    return urlopen(req).read().decode()


def _get_data(item_or_url):
    """ Get a binary item from url or _base_url
    """
    if '://' in item_or_url:
        url = item_or_url
    else:
        url = '%s/%s' % (_base_url, item_or_url)
    req = Request(url, headers={'User-Agent': 'flexx/%s' % flexx.__version__})
    return urlopen(req).read()


def _embed_css_resources(css, types=('.png',)):
    """ Replace urls in css with data urls
    """
    type_str = '|'.join('\%s' % t for t in types)
    rx = re.compile('(url\s*\(\s*(.*(%s))\s*\))' % type_str)
    found = rx.findall(css)
    for match, item, ext in found:
        data = base64.b64encode(_get_data(item)).decode()
        mime = mimetypes.types_map[ext]
        repl = 'url(data:%s;base64,%s)' % (mime, data)
        css = css.replace(match, repl)
    return css


app.assets.associate_asset(
    __name__,
    'leaflet.js',
    lambda: _get_code('leaflet.js'),
)
app.assets.associate_asset(
    __name__,
    'leaflet.css',
    lambda: _embed_css_resources(_get_code('leaflet.css')),
)
for icon in _leaflet_icons:
    app.assets.add_shared_data(icon, _get_data('images/%s' % icon))


class LeafletWidget(Widget):
    """ A widget that shows a slippy/tile-map using Leaflet.
    """
    
    layers = event.ListProp([], doc="""
        List of tilemap layer tuples: (url, 'Layer').
        """)
    
    zoom = event.IntProp(8, settable=True, doc="""
        Zoom level for the map.
        """)
    
    min_zoom = event.IntProp(0, settable=True, doc="""
        self zoom level for the map.
        """)
    
    max_zoom = event.IntProp(18, settable=True, doc="""
        Maximum zoom level for the map.
        """)
    
    center = event.FloatPairProp((5.2, 5.5), settable=True, doc="""
        The center of the map.
        """)
    
    show_layers = event.BoolProp(False, settable=True, doc="""
        Whether to show layers-icon on the top-right of the map.
        """)
    
    show_scale = event.BoolProp(False, settable=True, doc="""
        Whether to show scale at bottom-left of map.
        """)
    
    @event.action
    def add_layer(self, url, name=None):
        """ Add a layer to the map.
        """
        # Avoid duplicates
        self.remove_layer(url)
        if name:
            self.remove_layer(name)
        # Add layer
        layers = self.layers + [(url, name or 'Layer')]
        self._mutate_layers(layers)
    
    @event.action
    def remove_layer(self, url_or_name):
        """ Remove a layer from the map by url or name.
        """
        layers = list(self.layers)
        for i in reversed(range(len(layers))):
            if url_or_name in layers[i]:
                layers.pop(i)
        self._mutate_layers(layers)

    def _create_dom(self):
        global L
        node = window.document.createElement('div')
        self.mapnode = window.document.createElement('div')
        node.appendChild(self.mapnode)
        self.mapnode.id = 'maproot'
        self.mapnode.style.position = 'absolute'
        self.mapnode.style.top = '0px'
        self.mapnode.style.left = '0px'
        self.map = L.map(self.mapnode)
        self.map.on('zoomend', self.map_handle_zoom)
        self.map.on('moveend', self.map_handle_move)
        self.map.on('click', self.map_handle_mouse)
        self.map.on('dblclick', self.map_handle_mouse)
        # Container to keep track of leaflet layer objects
        self.layer_container = []
        self.layer_control = L.control.layers()
        self.scale = L.control.scale({'imperial': False, 'maxWidth': 200})
        # Set the path for icon images
        L.Icon.Default.prototype.options.imagePath = '_data/shared/'
        return node

    def map_handle_zoom(self, e):
        zoom = self.map.getZoom()
        if window.isNaN(zoom):
            return
        if zoom != self.zoom:
            self.set_zoom(zoom)

    def map_handle_move(self, e):
        center_coord = self.map.getCenter()
        center = center_coord.lat, center_coord.lng
        if center != self.center:
            self.set_center(center)

    def map_handle_mouse(self, e):
        latlng = [e.latlng.lat, e.latlng.lng]
        xy = [e.layerPoint.x, e.layerPoint.y]
        self.mouse_event(e.type, latlng, xy)

    @event.emitter
    def mouse_event(self, event, latlng, xy):
        return {'event': event, 'latlng': latlng, 'xy': xy}

    @event.reaction
    def __handle_zoom(self):
        self.map.setZoom(self.zoom)

    @event.reaction
    def __handle_min_zoom(self):
        self.map.setMinZoom(self.min_zoom)

    @event.reaction
    def __handle_max_zoom(self):
        self.map.setMaxZoom(self.max_zoom)

    @event.reaction
    def __handle_center(self):
        self.map.panTo(self.center)

    @event.reaction
    def __handle_show_layers(self):
        if self.show_layers:
            self.map.addControl(self.layer_control)
        else:
            self.map.removeControl(self.layer_control)

    @event.reaction
    def __handle_show_scale(self):
        if self.show_scale:
            self.map.addControl(self.scale)
        else:
            self.map.removeControl(self.scale)

    @event.reaction
    def __size_changed(self):
        size = self.size
        if size[0] or size[1]:
            self.mapnode.style.width = size[0] + 'px'
            self.mapnode.style.height = size[1] + 'px'
            # Notify the map that it's container's size changed
            self.map.invalidateSize()

    @event.reaction
    def __layers_changed(self):
        global L
        for layer in self.layer_container:
            self.layer_control.removeLayer(layer)
            if self.map.hasLayer(layer):
                self.map.removeLayer(layer)
        for layer_url, layer_name in self.layers:
            if not layer_url.endswith('.png'):
                if not layer_url.endswith('/'):
                    layer_url += '/'
                layer_url += '{z}/{x}/{y}.png'
            new_layer = L.tileLayer(layer_url)
            self.layer_container.append(new_layer)
            self.map.addLayer(new_layer)
            self.layer_control.addOverlay(new_layer, layer_name)


class LeafletExample(flexx.ui.Widget):

    def init(self):
        with flexx.ui.HBox():
            self.leaflet = LeafletWidget(
                flex=1,
                center=(52, 4.1),
                zoom=12,
                show_scale=lambda:self.cbs.checked,
                show_layers=lambda:self.cbl.checked,
            )
            with flexx.ui.VBox():
                self.btna = flexx.ui.Button(text='Add SeaMap')
                self.btnr = flexx.ui.Button(text='Remove SeaMap')
                self.cbs = flexx.ui.CheckBox(text='Show scale')
                self.cbl = flexx.ui.CheckBox(text='Show layers')
                self.list = flexx.ui.VBox()
                flexx.ui.Widget(flex=1)
        
        self.leaflet.add_layer('http://a.tile.openstreetmap.org/', 'OpenStreetMap')
    
    @event.reaction('btna.mouse_click')
    def handle_seamap_add(self, *events):
        self.leaflet.add_layer('http://t1.openseamap.org/seamark/', 'OpenSeaMap')

    @event.reaction('btnr.mouse_click')
    def handle_seamap_remove(self, *events):
        self.leaflet.remove_layer('http://t1.openseamap.org/seamark/', 'OpenSeaMap')

    # @event.reaction('cbs.checked', 'cbl.checked')
    # def handle_checkboxes(self, *events):
    #     self.leaflet.set_show_scale(self.cbs.checked
    #     self.leaflet.show_layers = self.cbl.checked

    @event.reaction('leaflet.mouse_event')
    def handle_leaflet_mouse(self, *events):
        global L
        ev = events[-1]
        latlng = tuple(ev['latlng'])
        flexx.ui.Label(text='%f, %f' % (int(100*latlng[0])/100, int(100*latlng[1])/100),
                       parent=self.list)
        latlng = tuple(ev['latlng'])
        if ev['event'] == 'click':
            m = L.marker(ev['latlng'])
            m.bindTooltip('%f, %f' % (latlng[0], latlng[1]))
            m.addTo(self.leaflet.map)


if __name__ == '__main__':
    app.launch(LeafletExample, 'app')
    app.run()

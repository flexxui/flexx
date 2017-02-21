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

    @event.prop
    def layers(self, layers=None):
        """ Array of tilemap layer urls.
        """
        # We expect the layers to be determined server side so
        # this can be a python only property
        if layers is None:
            layers = []
        if isinstance(layers, str):
            layers = [(layers, 'Layer')]
        if not isinstance(layers, list):
            layers = list(layers)
        for i, layer in enumerate(layers):
            if not isinstance(layer, tuple) and not isinstance(layer, list):
                layers[i] = (layer, 'Layer')
        return layers

    @event.prop
    def min_zoom(self, min_zoom=0):
        """ Minimum zoom level for the map
        """
        return int(min_zoom)

    @event.prop
    def max_zoom(self, max_zoom=18):
        """ Maximum zoom level for the map
        """
        return int(max_zoom)

    class Both:

        @event.prop
        def zoom(self, zoom=8):
            """ Zoom level for the map. This property is defined in Python and
            JS because the zoomlevel can be adjusted by the server as well as
            by the user through the map widget.
            """
            return int(zoom)

        @event.prop
        def center(self, center=(52.0, 5.5)):
            """ Center of the map. Can be set by the user panning the map, or by
            Python server code.
            """
            return float(center[0]), float(center[1])

        @event.prop
        def show_layers(self, show_layers=False):
            """ Show layers icon on the top-right of the map
            """
            return bool(show_layers)

        @event.prop
        def show_scale(self, show_scale=False):
            """ Show scale at bottom-left of map
            """
            return bool(show_scale)

    class JS:

        def _init_phosphor_and_node(self):
            self.phosphor = self._create_phosphor_widget('div')
            self.node = self.phosphor.node
            self.mapnode = window.document.createElement('div')
            self.node.appendChild(self.mapnode)
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

        def map_handle_zoom(self, e):
            zoom = self.map.getZoom()
            if window.isNaN(zoom):
                return
            if zoom != self.zoom:
                self.zoom = zoom

        def map_handle_move(self, e):
            center_coord = self.map.getCenter()
            center = center_coord.lat, center_coord.lng
            if center != self.center:
                self.center = center

        def map_handle_mouse(self, e):
            latlng = [e.latlng.lat, e.latlng.lng]
            xy = [e.layerPoint.x, e.layerPoint.y]
            self.mouse_event(e.type, latlng, xy)

        @event.emitter
        def mouse_event(self, event, latlng, xy):
            return {'event': event, 'latlng': latlng, 'xy': xy}

        @event.connect('zoom')
        def _handle_zoom(self, *events):
            self.map.setZoom(events[-1].new_value)

        @event.connect('min_zoom')
        def _handle_min_zoom(self, *events):
            self.map.setMinZoom(events[-1].new_value)

        @event.connect('max_zoom')
        def _handle_max_zoom(self, *events):
            self.map.setMaxZoom(events[-1].new_value)

        @event.connect('center')
        def _handle_center(self, *events):
            self.map.panTo(events[-1].new_value)

        @event.connect('show_layers')
        def _handle_show_layers(self, *events):
            if events[-1].new_value:
                self.map.addControl(self.layer_control)
            else:
                self.map.removeControl(self.layer_control)

        @event.connect('show_scale')
        def _handle_show_scale(self, *events):
            if events[-1].new_value:
                self.map.addControl(self.scale)
            else:
                self.map.removeControl(self.scale)

        @event.connect('size')
        def _size_changed(self, *events):
            size = self.size
            if size[0] or size[1]:
                self.mapnode.style.width = size[0] + 'px'
                self.mapnode.style.height = size[1] + 'px'
                # Notify the map that it's container's size changed
                self.map.invalidateSize()

        @event.connect('layers')
        def _layers_changed(self, *events):
            for layer in self.layer_container:
                self.layer_control.removeLayer(layer)
                if self.map.hasLayer(layer):
                    self.map.removeLayer(layer)
            for layer_url, layer_name in events[-1].new_value:
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
                layers=['http://a.tile.openstreetmap.org/'],
                center=(52, 4.1),
                zoom=12
            )
            with flexx.ui.VBox():
                self.btna = flexx.ui.Button(text='Add SeaMap')
                self.btnr = flexx.ui.Button(text='Remove SeaMap')
                self.cbs = flexx.ui.CheckBox(text='Show scale')
                self.cbl = flexx.ui.CheckBox(text='Show layers')
                self.list = flexx.ui.VBox()
                flexx.ui.Widget(flex=1)

    @event.connect('btna.mouse_click')
    def handle_seamap_add(self, *events):
        self.leaflet.layers = [
            ('http://a.tile.openstreetmap.org/', 'OpenStreetMap'),
            ('http://t1.openseamap.org/seamark/', 'OpenSeaMap'),
        ]

    @event.connect('btnr.mouse_click')
    def handle_seamap_remove(self, *events):
        self.leaflet.layers = [
            ('http://a.tile.openstreetmap.org/', 'OpenStreetMap'),
        ]

    @event.connect('cbs.checked', 'cbl.checked')
    def handle_checkboxes(self, *events):
        self.leaflet.show_scale = self.cbs.checked
        self.leaflet.show_layers = self.cbl.checked

    @event.connect('leaflet.mouse_event')
    def handle_leaflet_mouse(self, *events):
        ev = events[-1]
        latlng = tuple(ev['latlng'])
        flexx.ui.Label(text='%.5f, %.5f' % tuple(latlng), parent=self.list)

    class JS:
        @event.connect('leaflet.mouse_event')
        def handle_leaflet_mouse(self, *events):
            ev = events[-1]
            latlng = tuple(ev['latlng'])
            if ev['event'] == 'click':
                m = L.marker(ev['latlng'])
                m.bindTooltip('%f, %f' % (latlng[0], latlng[1]))
                m.addTo(self.leaflet.map)


if __name__ == '__main__':
    app.launch(LeafletExample, 'app')
    app.run()

"""
Simple example:

.. UIExample:: 300


    class Example(ui.Widget):

        def init(self):
            with ui.BoxPanel():
                ui.MapWidget(layers=['http://t1.openstreetmap.org/'],
                             zoom=8, center=[52.0, 5.5])

"""

from urllib.request import urlopen

import flexx
from flexx import event, app
from flexx.pyscript.stubs import window, L
from flexx.ui import Widget
from flexx.util.getresource import get_resource


_base_url = 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/'
_leaflet_version = '1.0.3'
_assets = (
    'leaflet.css',
    'leaflet.js',
    # Image assets are not (yet) supported (See #71)
    #    'images/marker-icon.png',
    #    'images/marker-icon-2x.png',
    #    'images/marker-shadow.png',
    #    'images/layers.png',
    #    'images/layers-2x.png',
)

for asset in _assets:
    app.assets.associate_asset(
        __name__,
        '%s/%s/%s' % (_base_url, _leaflet_version, asset)
    )


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
            JS because the zoomlevel can be adjust by the server as well as by
            the user through the map widget.
            """
            return int(zoom)

        @event.prop
        def center(self, center=(52.0, 5.5)):
            """ Center of the map. Can be set by the user panning the map, or by
            Python server code.
            """
            return float(center[0]), float(center[1])

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

        @event.connect('zoom')
        def _handle_zoom(self, *events):
            self.map.setZoom(self.zoom)

        @event.connect('min_zoom')
        def _handle_min_zoom(self, *events):
            self.map.setMinZoom(events[-1].new_value)

        @event.connect('max_zoom')
        def _handle_max_zoom(self, *events):
            self.map.setMaxZoom(events[-1].new_value)

        @event.connect('center')
        def _handle_center(self, *events):
            self.map.panTo(self.center)

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
            layers = []

            def add_layer_to_list(layer):
                layers.append(layer)

            self.map.eachLayer(add_layer_to_list)
            for layer in layers:
                self.map.removeLayer(layer)
            for layer in events[-1].new_value:
                if not layer.endswith('.png'):
                    if not layer.endswith('/'):
                        layer += '/'
                    layer += '{z}/{x}/{y}.png'
                lyr = L.tileLayer(layer)
                lyr.addTo(self.map)


if __name__ == '__main__':

    class MapWidget(flexx.ui.Widget):

        def init(self):
            with flexx.ui.HBox():
                self.map = LeafletWidget(
                    flex=1,
                    layers=['http://a.tile.openstreetmap.org/'],
                    center=(52, 4.1),
                    zoom=12
                )
                with flexx.ui.VBox():
                    self.btna = flexx.ui.Button(text='Add SeaMap')
                    self.btnr = flexx.ui.Button(text='Remove SeaMap')
                    flexx.ui.Widget(flex=1)

        @event.connect('btna.mouse_click')
        def handle_seamap_add(self, *events):
            self.map.layers = ['http://a.tile.openstreetmap.org/',
                               'http://t1.openseamap.org/seamark/']

        @event.connect('btnr.mouse_click')
        def handle_seamap_remove(self, *events):
            self.map.layers = ['http://a.tile.openstreetmap.org/']

    app.launch(MapWidget, 'xul')
    app.run()

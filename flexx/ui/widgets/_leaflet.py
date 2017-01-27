"""
Simple example:

.. UIExample:: 300
    
    
    class Example(ui.Widget):
        
        def init(self):
            with ui.BoxPanel():
                ui.MapWidget(layers=['http://t1.openstreetmap.org/'], 
                             zoom=8, center=[52.0, 5.5])

"""


import os

from ... import event, app
from ...pyscript.stubs import window, L
from . import Widget
from ...util.getresource import get_resource

# Associate leaflet assets
for asset_name in ('leaflet.css', 'leaflet.js'):
    code = get_resource(asset_name).decode()
    app.assets.associate_asset(__name__, asset_name, code)


class MapWidget(Widget):
    """ A widget that shows a slippy/tile-map using Leaflet.
    """

    @event.prop
    def layers(self, layers=None):
        """ Array of tilemap layer urls. 
        """
        if layers is None:
            layers = []
        return layers

    @event.prop
    def min_zoom(self, min_zoom=0):
        return int(min_zoom)

    @event.prop
    def max_zoom(self, max_zoom=18):
        return int(max_zoom)

    class Both:

        @event.prop
        def zoom(self, zoom=8):
            return int(zoom)

        @event.prop
        def center(self, center=(52.0, 5.5)):
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
            def remove_layer(layer):
                self.map.removeLayer(layer)
            # TODO: "remove_layer" modifies the layers contents. Check if
            # "eachLayer" appreciates that.
            self.map.eachLayer(remove_layer)
            for layer in events[-1].new_value:
                if layer[-4:] != '.png':
                    if layer[-1] != '/':
                        layer += '/'
                    layer += '{z}/{x}/{y}.png'
                lyr = L.tileLayer(layer)
                lyr.addTo(self.map)



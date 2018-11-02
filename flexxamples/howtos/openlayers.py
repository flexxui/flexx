# doc-export: OpenlayersExample
"""
Example demonstrating how to create a simple map app with Openlayers and flexx.

Features:

* Load geojson data to map.
* Draw points on map.
* Working with Openlayers events.

"""

import os
from flexx import flx

BASE_DIR = os.getcwd()

with open(BASE_DIR + '/static/js/data.json') as f:
    geojson = f.read()

ol_cdn = 'https://cdnjs.cloudflare.com/ajax/libs/openlayers/4.6.5/'
flx.assets.associate_asset(__name__, ol_cdn + 'ol.css')
flx.assets.associate_asset(__name__, ol_cdn + 'ol.js')


class Ol(flx.Widget):
    initialised = False

    @flx.action
    def remove_layers(self):
        self.map.removeLayer(self.vectorLayer)
        self.vectorLayer.getSource().clear()
        self.vectorLayer.getSource().refresh()

    @flx.action
    def add_drawing_interaction(self):
        self.map.addLayer(self.drawVectorLayer)
        self.map.addInteraction(self.drawPoint)

    @flx.action
    def remove_drawing_interaction(self):
        self.map.removeInteraction(self.drawPoint)
        self.map.removeLayer(self.drawVectorLayer)
        self.drawVectorLayer.getSource().clear()

    @flx.action
    def map_init(self):
        global ol
        if not self.initialised:
            self.olview = ol.View({
                "zoom": 8,
                "center": [-80.901813, 22.968599],
                "projection": "EPSG:4326",
                "minZoom": 3,
                "maxZoom": 100
            })

            self.baseLayer = ol.layer.Tile({
                "source": ol.source.OSM(),
            })

            self.vectorLayer = ol.layer.Vector({
                "source": ol.source.Vector({
                    "format": ol.format.GeoJSON()
                }),
                "name": "Vector",
                "style": ol.style.Style({
                    "image": ol.style.Circle({
                        "radius": 7,
                        "fill": ol.style.Fill({
                            "color": 'rgba(255, 0, 0, 0.5)'
                        })
                    })
                }),
            })

            self.drawVectorLayer = ol.layer.Vector({
                "source": ol.source.Vector({
                    "format": ol.format.GeoJSON()
                }),
                "name": "Draw Vector",
                "style": ol.style.Style({
                    "image": ol.style.Circle({
                        "radius": 7,
                        "fill": ol.style.Fill({
                            "color": 'rgba(0, 255, 0, 0.5)'
                        })
                    })
                }),
            })

            self.drawPoint = ol.interaction.Draw({
                "type": 'Point',
                "source": self.drawVectorLayer.getSource()
            })

            self.map_config = {
                "target": self.mapnode,
                'view': self.olview,
                "controls": [ol.control.Zoom(), ol.control.MousePosition()],
                "layers": []
            }
            self.map = ol.Map(self.map_config)
            self.map.on('click', self.pointer_event)
            self.initialised = True

    @flx.emitter
    def pointer_event(self, event):
        return {"event": event}

    @flx.action
    def add_vector_layer(self):
        format = self.vectorLayer.getSource().getFormat()
        features = format.readFeatures(geojson)
        self.vectorLayer.getSource().clear()
        self.vectorLayer.getSource().addFeatures(features)
        self.map.addLayer(self.vectorLayer)

    @flx.action
    def add_osm_layers(self):
        self.map.addLayer(self.baseLayer)

    def _create_dom(self):
        global document
        node = document.createElement('div')
        self.mapnode = document.createElement('div')
        node.appendChild(self.mapnode)
        self.mapnode.id = 'maproot'
        return node

    def _render_dom(self):
        self.map_init()
        return super()._render_dom()


class MainWidget(flx.Widget):
    def init(self):
        self.set_title("Openlayers example")
        with flx.VBox():
            with flx.HBox():
                self.map = Ol(flex=1)
                self.btn = flx.Button(text="", disabled=True)
                with flx.VBox():
                    self.btnosm = flx.Button(text='Load Openstreetmap')
                    self.btna = flx.Button(text='Load GEOJSON')
                    self.btnr = flx.Button(text='Remove GEOJSON')
                    self.btndraw = flx.Button(text='Draw Points')
                    self.btn_stop_draw = flx.Button(text='Stop Drawing')
                    flx.Widget(flex=1)
            self.coords = flx.Label(flex=1)

    @flx.reaction('btn_stop_draw.pointer_click')
    def handle_stop_drawing(self, *events):
        self.coords.set_text("Stop Drawing")
        self.map.remove_drawing_interaction()

    @flx.reaction('btndraw.pointer_click')
    def handle_drawing(self, *events):
        self.coords.set_text("Drawing..")
        self.map.add_drawing_interaction()

    @flx.reaction('btna.pointer_click')
    def handle_vector_layers(self, *events):
        self.coords.set_text("Adding GEOJSON")
        self.map.add_vector_layer()

    @flx.reaction('btnosm.pointer_click')
    def handle_osm_layers(self, *events):
        self.coords.set_text("Adding Openstreetmap")
        self.map.add_osm_layers()

    @flx.reaction('btnr.pointer_click')
    def handle_remove_layers(self, *events):
        self.map.remove_layers()
        self.coords.set_text("Removing GEOJSON")

    @flx.reaction('map.pointer_event')
    def map_click(self, *events):
        ev = events[-1]
        coord = ev['event']['coordinate']
        self.coords.set_text("Clicking on coordinate " + str(coord))


if __name__ == '__main__':
    flx.launch(MainWidget, 'firefox-browser')
    flx.run()

"""
Demo server.
"""

from flexx import app

from flexxamples.demos.monitor import Monitor
from flexxamples.demos.chatroom import ChatRoom
from flexxamples.demos.demo import Demo
from flexxamples.demos.colab_painting import ColabPainting
from flexxamples.demos.d3_collision import CollisionDemo
from flexxamples.demos.plotly_gdp import PlotlyGeoDemo


if __name__ == '__main__':
    # This example is setup as a server app
    app.serve(Monitor)
    app.serve(ChatRoom)
    app.serve(ColabPainting)
    app.serve(CollisionDemo)
    # app.serve(PlotlyGeoDemo)  # CORS fail?
    app.serve(Demo)
    app.start()

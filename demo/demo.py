"""
Demo server.
"""

import sys
import asyncio

from flexx import app

from flexxamples.demos.monitor import Monitor
from flexxamples.demos.chatroom import ChatRoom
from flexxamples.demos.demo import Demo
from flexxamples.demos.colab_painting import ColabPainting
from flexxamples.demos.d3_collision import CollisionDemo
from flexxamples.demos.plotly_gdp import PlotlyGeoDemo


async def exit_server_after_a_while():
    # Exit the server after 12 hours, after which it will start up again
    # (using Docker with auto-restart). This makes sure that the server
    # is not bother too much in case we have a memory leak.
    await asyncio.sleep(12 * 3600)
    sys.exit()


asyncio.ensure_future(exit_server_after_a_while())


if __name__ == "__main__":
    # This example is setup as a server app
    # app.serve(Monitor)
    # app.serve(ChatRoom)
    app.serve(ColabPainting)
    app.serve(CollisionDemo)
    # app.serve(PlotlyGeoDemo)  # CORS fail?
    app.serve(Demo)
    app.start()

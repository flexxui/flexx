"""
The Flexx application system.

The app module implements the connection between Python and JavaScript.
It runs a web server and websocket server based on Tornado, provides
an asset (and data) management system, and provides the PyComponent and
JsComponent classes, which form the basis for e.g. Widgets.
"""

_DEV_NOTES = """
Overview of classes:

* PyComponent and JsComponent: the base class for creating Python/JS component.
* JSModule: represents a module in JS that corresponds to a Python module.
* Asset: represents an asset.
* Bundle: an Asset subclass to represent a collecton of JSModule's in one asset.
* AssetStore: one instance of this class is used to provide all client
  assets in this process (JS, CSS, images, etc.). It also keeps track
  of modules.
* SessionAssets: base class for Session that implements the assets/data part.
* Session: object that handles connection between Python and JS. Has a
  websocket, and optionally a reference to the runtime.
* WebSocket: tornado WS handler.
* AppManager: keeps track of what apps are registered. Has functionality
  to instantiate apps and connect the websocket to them.
* Server: handles http requests. Uses manager to create new app
  instances or get the page for a pending session. Hosts assets by using
  the global asset store.
* Flexx class (in _clientcore.py): more or less the JS side of a session.

"""

import logging
logger = logging.getLogger(__name__)
del logging

# flake8: noqa
from ._app import App, manager
from ._asset import Asset, Bundle
from ._component2 import BaseAppComponent, LocalComponent, ProxyComponent
from ._component2 import PyComponent, JsComponent, StubComponent
from ._component2 import get_component_classes, LocalProperty

from ._funcs import run, start, stop
from ._funcs import init_notebook, serve, launch, export
from ._server import create_server, current_server
from ._session import Session
from ._modules import JSModule
from ._assetstore import assets
from ._clientcore import serializer

# Resolve cyclic dependencies, and explicit exports to help cx_Freeze
# from . import _tornadoserver -- no, we don't want Tornado unless really needed
from . import _component2
_component2.manager = manager

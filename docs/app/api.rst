App API
=======

Functions related to the event loop
-----------------------------------


.. autofunction:: flexx.app.start

.. autofunction:: flexx.app.run

.. autofunction:: flexx.app.stop

.. autofunction:: flexx.app.init_interactive

.. autofunction:: flexx.app.init_notebook

.. autofunction:: flexx.app.create_server

.. autofunction:: flexx.app.current_server


Functions related to us Component classes as apps
-------------------------------------------------

.. autofunction:: flexx.app.App

.. autofunction:: flexx.app.serve

.. autofunction:: flexx.app.launch

.. autofunction:: flexx.app.export

.. autofunction:: flexx.app.get_component_classes


The Component classes
---------------------

.. autoclass:: flexx.app.PyComponent
    :members:

.. autoclass:: flexx.app.JsComponent
    :members:


Session and Assets
------------------

An asset is represented using an ``Asset`` object that defines its sources,
dependencies, etc. Assets can be shared or specific to the session.
The AssetStore provides all shared assets for clients connected to the current
process. The global store is at ``flexx.app.assets``.
The session object handles the connection between Python and the JavaScript,
and it allows adding client-side assets, which for instance makes it
easy to create extensions based on existing JS libraries.



.. autoclass:: flexx.app.Asset
    :members:


.. autoclass:: flexx.app._assetstore.AssetStore
    :members:

.. autoclass:: flexx.app.Session
    :inherited-members:
    :members:

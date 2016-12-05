App API
=======

Functions related to the event loop
-----------------------------------


.. autofunction:: flexx.app.start

.. autofunction:: flexx.app.run

.. autofunction:: flexx.app.stop

.. autofunction:: flexx.app.init_interactive

.. autofunction:: flexx.app.init_notebook

.. autofunction:: flexx.app.call_later

.. autofunction:: flexx.app.create_server

.. autofunction:: flexx.app.current_server


Functions related to us Model classes as apps
---------------------------------------------

.. autofunction:: flexx.app.App

.. autofunction:: flexx.app.serve

.. autofunction:: flexx.app.launch

.. autofunction:: flexx.app.export

.. autofunction:: flexx.app.get_model_classes

.. autofunction:: flexx.app.get_active_model

.. autofunction:: flexx.app.get_active_models


The Model class
---------------

.. autoclass:: flexx.app.Model
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

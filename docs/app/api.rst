App API
=======

Functions related to the event loop
-----------------------------------


.. autofunction:: flexx.app.start

.. autofunction:: flexx.app.run

.. autofunction:: flexx.app.init_notebook

.. autofunction:: flexx.app.stop

.. autofunction:: flexx.app.call_later


The Model class
---------------

.. autoclass:: flexx.app.Model
    :members:

.. autofunction:: flexx.app.serve

.. autofunction:: flexx.app.launch

.. autofunction:: flexx.app.export

.. autofunction:: flexx.app.get_instance_by_id

.. autofunction:: flexx.app.get_model_classes


Session and Assets
------------------

The session handles the connection between Python and the JavaScript,
and it allows adding client-side assets, which for instance makes it
easy to create extensions based on existing JS libraries.

The AssetStore provides all assets for clients connected to the current
process. The global store is at ``flexx.app.assets``.

.. autoclass:: flexx.app.Session
    :inherited-members:
    :members:


.. autoclass:: flexx.app.assetstore.AssetStore
    :members:

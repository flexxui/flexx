------------------------
Handling assets and data
------------------------

Asset management
----------------

When writing code that relies on a certain JS or CSS library, that library
can be loaded in the client by associating it with the module that needs it.
Flexx will then automatically (and only) load it when code from that module is used in JS.
Flexx itself uses this mechanism is some widgets e.g. for Leaflet maps or the CodeMirror editor.


.. code-block:: py

    # Associate asset
    flx.assets.associate_asset(__name__, 'mydep.js', js_code)

    # Sometimes a more lightweight *remote* asset is prefered
    flx.assets.associate_asset(__name__, 'http://some.cdn/lib.css')

    # Create component (or Widget) that needs the asset at the client
    class MyComponent(flx.JsComponent):
        ....

It is also possible to provide assets that are not automatically loaded
on the main app page, e.g. for sub-pages or web workers:

.. code-block:: py

    # Register asset
    asset_url = flx.assets.add_shared_asset('mydep.js', js_code)


Data management
---------------

Data can be provided per session or shared between sessions:

.. code-block:: py

    # Add session-specific data. You need to call this inside a PyComponent
    # and use the link in the JS component that needs the data.
    link = my_component.session.add_data('some_name.png', binary_blob)

    # Add shared data. This can be called at the module level.
    link = flx.assets.add_shared_data('some_name.png', binary_blob)

Note that it is also possible to send data from Python to JS via an
action invokation (the data is send over the websocket in this case).
The latter also works for numpy arrays.

Next
----

Next up: :doc:`Sensible usage patterns <patterns>`.

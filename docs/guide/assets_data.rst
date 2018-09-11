------------------------
Handling assets and data
------------------------

Asset management
----------------

When writing code that relies on a certain JS or CSS library, that library
can be loaded in the client by associating it with the module that needs it.
Flexx will then automatically load it when code from that module is used in JS:

.. code-block:: py

    # Associate asset
    app.assets.associate_asset(__name__, 'mydep.js', js_code)

    # Sometimes a more lightweight *remote* asset is prefered
    app.assets.associate_asset(__name__, 'http://some.cdn/lib.css')

    # Create component (or Widget) that needs the asset at the client
    class MyComponent(app.JsComponent):
        ....

It is also possible to provide assets that are not automatically loaded
on the main app page, e.g. for sub-pages or web workers:

.. code-block:: py

    # Register asset
    asset_url = app.assets.add_shared_asset('mydep.js', js_code)


Data management
---------------

Data can be provided per session or shared between sessions:

.. code-block:: py

    # Add session-specific data
    link = my_component.session.add_data('some_name.png', binary_blob)

    # Add shared data
    link = app.assets.add_shared_data('some_name.png', binary_blob)

Note that it is also possible to send data from Python to JS via an
action invokation (the data is send over the websocket in this case).

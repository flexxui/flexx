Freezing Flexx apps
-------------------

Flexx needs special care when freezing, because it needs access to the Python
source code in order to compile it to JavaScript.

The easy way
============

There is experimental support to make freezing very easy:

.. code-block:: py

    from flexx import flx

    class Example(flx.Widget):
        def init(self):
            flx.Button(text="Hi there")

    if __name__ == "__main__":
        app = flx.App(Example)
        app.freeze("~/Desktop/flexx_apps")


The more explicit way
=====================

The above approach does most of the magic behind the scenes. For more control,
you can also use a more explicit approach.

First, create a script that represents your application entry point. It
is important that this script does not define any new Flexx widgets. It
should look something like this:

.. code-block:: py

    # Install hook so we we can import modules from source when frozen.
    from flexx.util import freeze
    freeze.install()

    # Run your app as usual
    from flexx import flx
    from my_module import MyWidget
    app = flx.App(MyWidget)
    app.launch("firefox-app")
    flx.run()


Next, use ``PyInstaller`` as usual to create an app directory. Consider
using ``--exclude-module numpy`` (PyInstaller thinks that Flexx needs Numpy, but this not the case).

Next, copy the source code of the modules that define Flexx widgets. If you
run PyInstaller from a script (using ``PyInstaller.__main__.run()``) then you
can combine it.

.. code-block:: py

    from flexx.util import freeze

    freeze.copy_module("flexx", app_dir)  # always
    freeze.copy_module("flexxamples", app_dir)  # used something from here?
    freeze.copy_module("my_module", app_dir)

That should be it!

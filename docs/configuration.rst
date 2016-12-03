-----------------
Configuring Flexx
-----------------

This page lists the configuration options available to Flexx, implemented
via the :class:`Config <flexx.util.config.Config>` class. Configuration
options are read from ``<appdata>/.flexx.cfg`` (check
``flexx.util.config.appdata_dir()`` for the actual location),
and can also be set using
environment variables and command line arguments, as explained below.
Alternatively, options can be set directly in Python via
``flexx.config.foo = 3``.

.. autodata:: flexx.config
    :annotation:

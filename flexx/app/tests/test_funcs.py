from flexx.util.testing import run_tests_if_main, raises

from flexx import app


def test_add_handlers():
    server = app.init()
    tornado_app = server.native
    assert tornado_app.add_handlers

run_tests_if_main()

from flexx.util.testing import run_tests_if_main, raises

from flexx import app


class Fooo1(app.Model):
    pass


def test_get_model_instance_by_id():
    # is really a test for the session, but historically, the test is done here
    
    # This test needs a default session
    session = app.manager.get_default_session()
    if session is None:
        session = app.manager.create_default_session()
    
    m1 = Fooo1()
    m2 = Fooo1()
    
    assert m1 is not m2
    assert session.get_model_instance_by_id(m1.id) is m1
    assert session.get_model_instance_by_id(m2.id) is m2
    assert session.get_model_instance_by_id('blaaaa') is None


run_tests_if_main()

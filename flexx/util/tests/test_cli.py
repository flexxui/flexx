import sys
import subprocess
import flexx

from flexx.util.testing import run_tests_if_main, raises


def test_cli():
    cmd = [sys.executable, '-m', 'flexx', 'version']
    v = subprocess.check_output(cmd, stderr=subprocess.STDOUT).decode().strip()
    assert v == flexx.__version__


run_tests_if_main()

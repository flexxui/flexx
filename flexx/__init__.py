__version__ = '0.8.0'

# Assert compatibility
import sys
if sys.version_info < (3, 5):  # pragma: no cover
    raise RuntimeError('Flexx needs at least Python 3.5')

# Import config object
from ._config import config  # noqa
from .util.logging import set_log_level  # noqa
set_log_level(config.log_level)

del sys

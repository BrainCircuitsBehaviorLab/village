from contextlib import suppress
from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("village")
except PackageNotFoundError:
    __version__ = "0.0.0"

"""Mock heavy optional dependencies so unit tests run without a display."""

import sys
from unittest.mock import MagicMock

for mod in [
    "PyQt5",
    "PyQt5.QtCore",
    "PyQt5.QtGui",
    "PyQt5.QtWidgets",
    "cv2",
    "scipy",
    "scipy.interpolate",
]:
    sys.modules.setdefault(mod, MagicMock())

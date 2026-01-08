
import sys
import types
from unittest.mock import MagicMock

# Mock modules to match Sphinx environment
sys.modules["cv2"] = MagicMock()
sys.modules["PyQt5"] = MagicMock()
sys.modules["PyQt5.QtCore"] = MagicMock()
sys.modules["PyQt5.QtGui"] = MagicMock()
sys.modules["PyQt5.QtWidgets"] = MagicMock()
sys.modules["pandas"] = MagicMock()
sys.modules["numpy"] = MagicMock()
sys.modules["numpy"].__version__ = "1.21.0"
sys.modules["scipy"] = MagicMock()
sys.modules["scipy"].__version__ = "1.7.0"
sys.modules["scipy.interpolate"] = MagicMock()
sys.modules["scipy.io"] = MagicMock()
sys.modules["smbus2"] = MagicMock()
sys.modules["fire"] = MagicMock()
sys.modules["calplot"] = MagicMock()
sys.modules["serial"] = MagicMock()
sys.modules["sounddevice"] = MagicMock()
sys.modules["matplotlib"] = MagicMock()
sys.modules["matplotlib.pyplot"] = MagicMock()
sys.modules["matplotlib.backends"] = MagicMock()
sys.modules["matplotlib.backends.backend_qt5agg"] = MagicMock()
sys.modules["matplotlib.figure"] = MagicMock()

# Add project root to sys.path
sys.path.insert(0, "/home/hmv/village")

print("Importing village.gui.data_layout...")
try:
    import village.gui.data_layout
    print("Importing village.screen.video_worker...")
    import village.screen.video_worker
    print("Import successful!")
except Exception:
    import traceback
    traceback.print_exc()

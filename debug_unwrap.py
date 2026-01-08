import sys
import inspect
from unittest.mock import MagicMock

# Simulate Sphinx mocking
mock_qt_core = MagicMock()
sys.modules["PyQt5.QtCore"] = mock_qt_core

# In the user's code: from PyQt5.QtCore import pyqtSignal
pyqtSignal = mock_qt_core.pyqtSignal

print(f"pyqtSignal type: {type(pyqtSignal)}")
print("Attempting inspect.unwrap(pyqtSignal)...")
try:
    # Set a timeout/recursion limit concept or just run it and see if it hangs?
    # inspect.unwrap iterates until __wrapped__ is gone.
    # If MagicMock returns itself for accessing __wrapped__, it loops.
    
    # Configure mock to be nasty if needed, but plain MagicMock might be enough if configured by Sphinx?
    # Sphinx's mock usually just returns MagicMocks for everything.
    
    unwrapped = inspect.unwrap(pyqtSignal)
    print("Unwrap successful.")
except ValueError as e:
    print(f"Caught expected error: {e}")
except RecursionError:
    print("Caught RecursionError (loop)")
except Exception as e:
    print(f"Caught unexpected error: {e}")

# Also test on an instance
signal_instance = pyqtSignal()
print(f"signal_instance type: {type(signal_instance)}")
print("Attempting inspect.unwrap(signal_instance)...")
try:
    unwrapped_inst = inspect.unwrap(signal_instance)
    print("Unwrap instance successful.")
except Exception as e:
    print(f"Instance unwrap error: {e}")

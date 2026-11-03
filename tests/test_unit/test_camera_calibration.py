"""Tests for the printable grid of the camera calibration."""

import importlib
import re
import sys
from types import ModuleType
from unittest.mock import MagicMock

import matplotlib
import pytest

matplotlib.use("Agg")

MODULE = "village.calibration.camera_calibration"


@pytest.fixture
def camera_calibration(monkeypatch) -> ModuleType:
    """The module, with the GUI modules it imports replaced by mocks (importing
    them would start the whole application): the grid functions don't use
    them. Everything is restored after the test."""
    monkeypatch.setitem(
        sys.modules,
        "village.custom_classes.calibration_base",
        MagicMock(CalibrationBase=object),
    )
    monkeypatch.setitem(sys.modules, "village.gui.layout", MagicMock(Layout=object))
    monkeypatch.setitem(sys.modules, "village.scripts.utils", MagicMock())
    monkeypatch.delitem(sys.modules, MODULE, raising=False)
    module = importlib.import_module(MODULE)
    monkeypatch.setitem(sys.modules, MODULE, module)
    return module


def test_grid_dimensions_a4_complete_dots(camera_calibration) -> None:
    assert camera_calibration.grid_dimensions(210, 297, 50, 15) == (4, 6)


def test_grid_dimensions_a4_no_margin(camera_calibration) -> None:
    assert camera_calibration.grid_dimensions(210, 297, 50, 0) == (5, 6)


def test_pdf_has_the_requested_page_size(camera_calibration, tmp_path) -> None:
    """1 mm in the grid must be 1 mm on the page, or the spacing is wrong."""
    out = camera_calibration.make_circle_grid(
        210, 297, out_path=str(tmp_path / "grid.pdf")
    )
    box = re.search(rb"MediaBox\s*\[\s*0\s+0\s+([\d.]+)\s+([\d.]+)", out.read_bytes())
    assert box is not None
    assert abs(float(box[1]) / 72 * 25.4 - 210) < 0.1
    assert abs(float(box[2]) / 72 * 25.4 - 297) < 0.1

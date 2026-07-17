# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

import os
import pathlib
import sys
from unittest.mock import MagicMock

import setuptools_scm  # type: ignore

# Some village modules touch the filesystem (mkdir/makedirs) as a side effect
# of module-level singleton instantiation (e.g. `manager = Manager()`), using
# default paths like /home/<user>/... that only exist on the real device.
# Silence those failures here so the modules can still be imported (and thus
# documented) on any machine running the docs build.
_orig_os_makedirs = os.makedirs
_orig_path_mkdir = pathlib.Path.mkdir


def _safe_os_makedirs(name, *args, **kwargs):
    try:
        return _orig_os_makedirs(name, *args, **kwargs)
    except OSError:
        return None


def _safe_path_mkdir(self, *args, **kwargs):
    try:
        return _orig_path_mkdir(self, *args, **kwargs)
    except OSError:
        return None


os.makedirs = _safe_os_makedirs
pathlib.Path.mkdir = _safe_path_mkdir


# Manually mock PyQt5 to avoid infinite recursion in sphinx-autodoc-typehints
# when unwrapping pyqtSignal/pyqtSlot.
class MockSignal:
    def __init__(self, *args, **kwargs):
        pass

    def connect(self, *args, **kwargs):
        pass

    def emit(self, *args, **kwargs):
        pass


class MockSlot:
    def __init__(self, *args, **kwargs):
        pass

    def __call__(self, *args, **kwargs):
        if len(args) == 1 and callable(args[0]):
            return args[0]
        return self


mock_qt = MagicMock()
mock_core = MagicMock()
mock_core.pyqtSignal = MockSignal
mock_core.pyqtSlot = MockSlot
mock_core.QObject = object
# Add other widely used QtCore classes to avoid AttributeErrors if needed,
# although MagicMock handles attributes automatically.
# We explicitly set QObject to object to allow inheritance without issues.

sys.modules["PyQt5"] = mock_qt
sys.modules["PyQt5.QtCore"] = mock_core
sys.modules["PyQt5.QtGui"] = MagicMock()
sys.modules["PyQt5.QtWidgets"] = MagicMock()

# Mock controllers and hardware-specific modules that create hardware connections
# at module-level import time. These only run on Raspberry Pi and fail on macOS
# with OSError [Errno 45] or ModuleNotFoundError for Linux-only libraries.
sys.modules["village.controllers.arduino_controller"] = MagicMock()
sys.modules["village.controllers.bpod_controller"] = MagicMock()
sys.modules["village.controllers.trial_recorder"] = MagicMock()

# Used when building API docs, put the dependencies
# of any class you are documenting here
autodoc_mock_imports = [
    "numpy",
    "pandas",
    "PyQt5",
    "PyQt5.QtCore",
    "PyQt5.QtGui",
    "PyQt5.QtWidgets",
    "cv2",
    "serial",
    "smbus2",
    "telegram",
    "scipy",
    "scipy.interpolate",
    "fire",
    "calplot",
    "matplotlib",
    "matplotlib.pyplot",
    "matplotlib.dates",
    "matplotlib.figure",
    "jinja2",
    "seaborn",
    "PyQt6",
    "gpiod",
    "picamera2",
    "libcamera",
    "PCA9685_smbus2",
    "pi5neo",
    "evdev",
    "pyalsaaudio",
    "pyarrow",
    "pyarrow.parquet",
    "ahrs",
    "ahrs.common",
    "ahrs.common.orientation",
    "ahrs.filters",
    "bleak",
    "bleak.backends",
    "bleak.backends.device",
    "BpodPorts",
    "utils_functions",
]

# Add the module path to sys.path here.
# If the directory is relative to the documentation root,
# use os.path.abspath to make it absolute, like shown here.
sys.path.insert(0, os.path.abspath("../.."))

# village.settings hardcodes /home/<user>/village_projects/... as the default
# project directory. That path only exists on the real device, so redirect
# every directory-flavoured default to a writable temp dir before any other
# village module (which may instantiate singletons that write to disk on
# import) gets imported.
import tempfile  # noqa: E402

import village.settings as _village_settings  # noqa: E402
from village.classes.settings_class import SuperEnum  # noqa: E402

_safe_project_root = os.path.join(tempfile.gettempdir(), "village_docs_build")
os.makedirs(_safe_project_root, exist_ok=True)
for _setting in _village_settings.settings.all_settings:
    if isinstance(_setting.value, str) and _setting.value.startswith(
        _village_settings.default_project_directory
    ):
        _setting.value = _setting.value.replace(
            _village_settings.default_project_directory, _safe_project_root, 1
        )
    # Settings.get() only converts the saved-QSettings string to the proper
    # enum when a value was actually saved; its fallback (no value saved, the
    # common case for a docs build) returns the raw factory string untouched.
    # Some modules call settings.get(...).name at import time, which then
    # crashes on a plain str. Pre-convert those factory strings here.
    if (
        isinstance(_setting.value, str)
        and isinstance(_setting.value_type, type)
        and issubclass(_setting.value_type, SuperEnum)
    ):
        try:
            _setting.value = _setting.value_type(_setting.value)
        except ValueError:
            pass

# Autodoc configuration to handle circular imports
autodoc_default_options = {
    "members": True,
    "member-order": "bysource",
    "undoc-members": True,
    "show-inheritance": True,
    "no-index": True,
}

# Don't execute code during import (helps avoid circular import side effects)
autodoc_preserve_defaults = True

project = "village"
copyright = "2024, Brain Circuits & Behavior Lab"
author = "Rafael Marin"
try:
    release = setuptools_scm.get_version(root="../..", relative_to=__file__)
except LookupError:
    # if git is not initialised, still allow local build
    # with a dummy version
    release = "0.0.0"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.napoleon",
    "sphinx.ext.autodoc",
    "sphinx.ext.githubpages",
    # "sphinx_autodoc_typehints",  # Disabled: conflicts with autodoc_mock_imports
    "sphinx.ext.autosummary",
    "sphinx.ext.viewcode",
    "sphinx.ext.intersphinx",
    "sphinx.ext.autosectionlabel",
    "sphinxcontrib.video",
    "sphinx_sitemap",
    "sphinx_design",
    "myst_parser",
    "nbsphinx",
]

# Configure the myst parser to enable cool markdown features
# See https://sphinx-design.readthedocs.io
myst_enable_extensions = [
    "amsmath",
    "colon_fence",
    "deflist",
    "dollarmath",
    "fieldlist",
    "html_admonition",
    "html_image",
    "linkify",
    "replacements",
    "smartquotes",
    "strikethrough",
    "substitution",
    "tasklist",
]
# Automatically add anchors to markdown headings
myst_heading_anchors = 3


# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# Automatically generate stub pages for API
autosummary_generate = True
autodoc_default_flags = ["members", "inherited-members"]

# Remove module names from class documentation
add_module_names = False

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = [
    "**.ipynb_checkpoints",
    # to ensure that include files (partial pages) aren't built, exclude them
    # https://github.com/sphinx-doc/sphinx/issues/1965#issuecomment-124732907
    "**/includes/**",
    "**/pybpodapi/**",
    "main/welcome.md",
]

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "shibuya"

html_title = "Training village"

html_theme_options = {
    "light_logo": "_static/logo_light.svg",
    "dark_logo": "_static/logo_dark.svg",
    "color_mode": "light",
    "github_url": "https://github.com/BrainCircuitsBehaviorLab/village",
    "nav_links": [
        {"title": "Documentation", "url": "overview/system"},
        {"title": "API", "url": "api_index"},
        {"title": "Resources", "url": "resources/list_of_parts"},
        {"title": "FAQ", "url": "faq/faq"},
    ],
}

html_sidebars = {
    "index": [],
    "**": ["sidebars/localtoc.html"],
}

html_permalinks = False
html_show_copyright = False
html_show_sphinx = False


# Redirect the webpage to another URL
# Sphinx will create the appropriate CNAME file in the build directory
# The default is the URL of the GitHub pages
# https://www.sphinx-doc.org/en/master/usage/extensions/githubpages.html
github_user = "BrainCircuitsBehaviorLab"
html_baseurl = f"https://{github_user}.github.io/{project}"
sitemap_url_scheme = "{link}"

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ["_static"]
html_favicon = "_static/favicon.svg"
html_css_files = ["custom.css"]
html_js_files = ["lightbox.js", "chatbot-widget.js"]

# Ignore links and anchors
linkcheck_ignore = [
    "https://www.raspberrypi.com/*",
    "https://help.realvnc.com/hc/en-us/articles/360029619052-Activating-a-RealVNC-Connect-Lite-subscription",
    "https://www.gnu.org/licenses/quick-guide-gplv3.pdf",
]
linkcheck_anchors_ignore_for_url = [
    "https://github.com/neuroinformatics-unit/actions/tree/v2/build_sphinx_docs",
]

autosectionlabel_prefix_document = True

suppress_warnings = [
    "docutils",
    "image.not_readable",
    "myst.header",
    "autosummary",
    "ref.duplicate",
    "ref.python",
]

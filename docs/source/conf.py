# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

import os
import sys
import setuptools_scm  # type: ignore
from unittest.mock import MagicMock

# Manually mock PyQt5 to avoid infinite recursion in sphinx-autodoc-typehints
# when unwrapping pyqtSignal/pyqtSlot.
class MockSignal:
    def __init__(self, *args, **kwargs): pass
    def connect(self, *args, **kwargs): pass
    def emit(self, *args, **kwargs): pass

class MockSlot:
    def __init__(self, *args, **kwargs): pass
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
    "sounddevice",
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
]

# Add the module path to sys.path here.
# If the directory is relative to the documentation root,
# use os.path.abspath to make it absolute, like shown here.
sys.path.insert(0, os.path.abspath("../.."))

# Autodoc configuration to handle circular imports
autodoc_default_options = {
    'members': True,
    'member-order': 'bysource',
    'undoc-members': True,
    'show-inheritance': True,
}

# Don't execute code during import (helps avoid circular import side effects)
autodoc_preserve_defaults = True

project = "village"
copyright = "2024, Rafael Marin, Balma Serrano, Hernando Vergara, Jaime de la Rocha"
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

suppress_warnings = ['autosummary', 'ref.duplicate']

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
]

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "shibuya"

html_title = "Training village"

html_theme_options = {
    "light_logo": "_static/logo.png",
    "dark_logo": "_static/logo.png",
    "color_mode": "light",
    "github_url": "https://github.com/BrainCircuitsBehaviorLab/village",
    "nav_links": [
        {"title": "Documentation", "url": "initial_setup/prerequisites"},
    ],
}

html_sidebars = {
    "index": [],
    "**": ["sidebars/localtoc.html"],
}

html_permalinks = False


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

suppress_warnings = ["docutils"]

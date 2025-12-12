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

MOCK_MODULES = [
    "numpy",
    "pandas",
    "cv2",
    "serial",
    "smbus2",
    "sounddevice",
    "telegram",
    "scipy",
    "fire",
    "calplot",
]

for mod_name in MOCK_MODULES:
    mock = MagicMock()
    mock.__name__ = mod_name
    mock.__file__ = "mock"
    mock.__path__ = ["mock"]
    sys.modules[mod_name] = mock

# Used when building API docs, put the dependencies
# of any class you are documenting here
autodoc_mock_imports = MOCK_MODULES

# Add the module path to sys.path here.
# If the directory is relative to the documentation root,
# use os.path.abspath to make it absolute, like shown here.
sys.path.insert(0, os.path.abspath("../.."))

project = "village"
copyright = "2024, Rafael Marin, Balma Serrano, Hernando Vergara"
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
    "sphinx_autodoc_typehints",
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
]

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

# html_theme = "sphinxawesome_theme"
# html_theme = "sphinx_book_theme"
html_theme = "furo"

html_title = "Training village"


github_icon = (
    '<svg height="26px" style="margin-top:-2px;display:inline" '
    'viewBox="0 0 45 44" '
    'fill="currentColor" xmlns="http://www.w3.org/2000/svg">'
    '<path fill-rule="evenodd" clip-rule="evenodd" '
    'd="M22.477.927C10.485.927.76 10.65.76 22.647c0 9.596 6.223 17.736 '
    "14.853 20.608 1.087.2 1.483-.47 1.483-1.047 "
    "0-.516-.019-1.881-.03-3.693-6.04 "
    "1.312-7.315-2.912-7.315-2.912-.988-2.51-2.412-3.178-2.412-3.178-1.972-1.346.149-1.32.149-1.32 "  # noqa
    "2.18.154 3.327 2.24 3.327 2.24 1.937 3.318 5.084 2.36 6.321 "
    "1.803.197-1.403.759-2.36 "
    "1.379-2.903-4.823-.548-9.894-2.412-9.894-10.734 "
    "0-2.37.847-4.31 2.236-5.828-.224-.55-.969-2.759.214-5.748 0 0 "
    "1.822-.584 5.972 2.226 "
    "1.732-.482 3.59-.722 5.437-.732 1.845.01 3.703.25 5.437.732 "
    "4.147-2.81 5.967-2.226 "
    "5.967-2.226 1.185 2.99.44 5.198.217 5.748 1.392 1.517 2.232 3.457 "
    "2.232 5.828 0 "
    "8.344-5.078 10.18-9.916 10.717.779.67 1.474 1.996 1.474 4.021 0 "
    "2.904-.027 5.247-.027 "
    "5.96 0 .58.392 1.256 1.493 1.044C37.981 40.375 44.2 32.24 44.2 "
    '22.647c0-11.996-9.726-21.72-21.722-21.72" '
    'fill="currentColor"/></svg>'
)

html_logo = "_static/logo.png"

html_theme_options = {
    # "secondary_sidebar_items": {
    #     # Para quitar en todas las páginas el toc: "**": [],
    #     # Para quitarlo en alguna página en concreto: nombre_de_la_pagina: []
    #     "**": [],
    #     # "**": ["page-toc"],
    #     # "index": [],
    # },
    # "home_page_in_toc": True,
    # "use_download_button": False,  # True si quieres que aparezca el botón de descarga
    # "logo_light": "_static/favicon.svg",
    # "logo_dark": "_static/favicon-white.svg",
    # "light_logo": "logo.png",
    # "dark_logo": "logo.png",
    "globaltoc_includehidden": True,
    "body_max_width": "none",
    # "page_width": "auto",
    "sidebar_hide_name": True,
}
html_permalinks = False

# html_theme_options = {
#     "collapse_navigation": False,
#     "sticky_navigation": False,
#     "navigation_depth": 4,
#     "titles_only": False,
# }


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

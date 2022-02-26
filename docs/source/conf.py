#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# ProbNum documentation build configuration file, created by
# sphinx-quickstart on Fri Nov  2 15:54:04 2019.
#
# This file is execfile()d with the current directory set to its
# containing dir.
#
# Note that not all possible configuration values are present in this
# autogenerated file.
#
# All configuration values have a default; values that are commented out
# serve to show the default.

from datetime import datetime
import os
from pathlib import Path
import sys

from pkg_resources import DistributionNotFound, get_distribution

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
sys.path.insert(0, os.path.abspath("../src"))
sys.path.append(os.path.abspath("./_ext"))

# -- General configuration ------------------------------------------------

# If your documentation needs a minimal Sphinx version, state it here.
needs_sphinx = "3.0"

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "sphinx.ext.napoleon",
    "sphinx.ext.doctest",
    "sphinx.ext.intersphinx",
    "sphinx.ext.todo",
    "sphinx.ext.coverage",
    "sphinx.ext.mathjax",
    "sphinx.ext.viewcode",
    "sphinx_automodapi.automodapi",
    "sphinx_autodoc_typehints",
    "sphinxcontrib.bibtex",
    "sphinx_gallery.load_style",
    "myst_parser",
    "nbsphinx",
    "probnum-config-options",
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# Settings for napoleon
napoleon_use_param = True

# Remove possible duplicate methods when using 'automodapi'
# autodoc_default_flags = ['no-members']
numpydoc_show_class_members = True

# Settings for automodapi
automodapi_toctreedirnm = "api/automod"
automodapi_writereprocessed = False
automodsumm_inherited_members = True

# Settings for autodoc_typehints
typehints_fully_qualified = False
typehints_document_rtype = True

# The suffix(es) of source filenames.
# You can specify multiple suffixes as a list of strings:
source_suffix = [".rst", ".md", ".ipynb"]

# The master toctree document.
master_doc = "sitemap"

# General information about the project.
project = "probnum"
copyright = str(datetime.utcnow().year)
author = "ProbNum Authors"

# The version info for the project you're documenting, acts as replacement for
# |version| and |release|, also used in various other places throughout the
# built documents.

try:
    # The full version, including alpha/beta/rc tags.
    release = get_distribution(project).version
    # The short X.Y.Z version.
    version = ".".join(release.split(".")[:2])
except DistributionNotFound:
    version = ""
finally:
    del get_distribution, DistributionNotFound

# The language for content autogenerated by Sphinx. Refer to documentation
# for a list of supported languages.
#
# This is also used if you do content translation via gettext catalogs.
# Usually you set "language" from the command line for these cases.
language = "en"

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This patterns also effect to html_static_path and html_extra_path
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store", "**.ipynb_checkpoints"]

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = "default"

# If true, `todo` and `todoList` produce output, else they produce nothing.
todo_include_todos = True

# -- Jupyter notebooks (nbsphinx) ------------------------------

# Work-around until https://github.com/sphinx-doc/sphinx/issues/4229 is solved:
html_scaled_image_link = False

# Don't add .txt suffix to source files:
html_sourcelink_suffix = ""

# Allow errors in the build process
nbsphinx_allow_errors = True

# Whether to execute notebooks before conversion or not.
# Possible values: 'always', 'never', 'auto' (default).
nbsphinx_execute = "auto"

# List of arguments to be passed to the kernel that executes the notebooks:
nbsphinx_execute_arguments = [
    "--InlineBackend.figure_formats={'svg', 'pdf'}",  # e.g. for matplotlib plots
    "--InlineBackend.rc={'figure.dpi': 150}",
]

# -- Intersphinx configuration ----------------------------------------------

# Whenever Sphinx encounters a cross-reference that has no matching target in the
# current documentation set, it looks for targets in 'intersphinx_mapping'. A reference
# like :py:class:`zipfile.ZipFile` can then link to the Python documentation for the
# ZipFile class.
intersphinx_mapping = {
    "python": ("https://docs.python.org/3/", None),
    "numpy": ("https://numpy.org/doc/stable/", None),
    "scipy": ("https://docs.scipy.org/doc/scipy", None),
    "matplotlib": ("https://matplotlib.org/", None),
}

# -- Options for HTML output ----------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
html_theme = "pydata_sphinx_theme"

html_title = f"{project} {version} documentation"
html_context = {
    "AUTHOR": author,
    "DESCRIPTION": "ProbNum: Probabilistic Numerics in Python.",
    "SITEMAP_BASE_URL": "http://probnum.org/",  # Trailing slash is needed
    "VERSION": version,
}

# (Optional) Logo. Should be small enough to fit the navbar (ideally 24x24).
# Path should be relative to the ``_static`` files directory.
html_logo = "assets/img/logo/probnum_logo_light_txtright.svg"

# Theme options are theme-specific and customize the look and feel of a theme
# further. For a list of options available for each theme, see the
# documentation.
html_theme_options = {
    "navbar_align": "right",
    "show_toc_level": 3,
    "navigation_depth": 4,
    "external_links": [
        {
            "name": "Probabilistic Numerics",
            "url": "https://probabilistic-numerics.github.io/website/",
        },
    ],
    "icon_links": [
        {
            "name": "GitHub",
            "url": "https://github.com/probabilistic-numerics/probnum",
            "icon": "fab fa-github",
        },
        {
            "name": "PyPI",
            "url": "https://pypi.org/project/probnum",
            "icon": "fab fa-python",
        },
    ],
}

# The name of an image file (within the static path) to use as favicon of the
# docs.  This file should be a Windows icon file (.ico) being 16x16 or 32x32
# pixels large.
html_favicon = "assets/img/favicons/favicon.ico"

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ["_static", "assets"]
html_css_files = ["custom.css"]

# Additional pages generated from .html files
html_additional_pages = {"index": "index.html"}

# Custom sidebar templates, maps document names to template names.
html_sidebars = {
    "index": [],
    "probnum/*": [],
    "community/*": [],
}

# Inheritance graphs generated by graphviz
graphviz_output_format = "svg"
inheritance_graph_attrs = dict(size='""')  # resize graphs correctly

# Sphinx gallery configuration
sphinx_gallery_conf = {
    "default_thumb_file": "assets/img/logo/probnum_logo.png",  # default thumbnail image
}

# MyST configuration
myst_update_mathjax = False  # needed for mathjax compatibility with nbsphinx
myst_enable_extensions = ["dollarmath", "amsmath"]

# Sphinx Bibtex configuration
bibtex_bibfiles = []
for f in Path("research/bibliography").glob("*.bib"):
    bibtex_bibfiles.append(str(f))
bibtex_default_style = "unsrtalpha"
bibtex_reference_style = "label"
bibtex_encoding = "utf-8-sig"

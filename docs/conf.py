"""Sphinx configuration for EPMaps documentation."""

import sys
from pathlib import Path

# Add project root to path for autodoc
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

# Project information
project = "EPMaps"
copyright = "2026, Santiago Andrade"
author = "Santiago Andrade"
release = "0.1.0"

# Extensions
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.napoleon",
    "sphinx_autodoc_typehints",
]

# Autodoc settings
autodoc_typehints = "description"
autodoc_member_order = "bysource"
autosummary_generate = True

# Napoleon settings (Google-style docstrings)
napoleon_google_docstring = True
napoleon_numpy_docstring = False
napoleon_include_init_docstring = False
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = True
napoleon_use_admonition_for_examples = False
napoleon_use_admonition_for_notes = False
napoleon_use_admonition_for_references = False
napoleon_use_ivar = False
napoleon_use_param = True
napoleon_use_rtype = True

# HTML theme
html_theme = "sphinx_rtd_theme"
html_theme_options = {
    "logo_only": False,
    "display_version": True,
    "prev_next_buttons_location": "bottom",
    "style_external_links": False,
    "vcs_pageview_mode": "",
    "style_nav_header_background": "#2980B9",
}

# HTML output options
html_static_path = []
html_last_updated_format = "%Y-%m-%d"
html_show_sphinx = False

# Paths
templates_path = ["_templates"]
exclude_patterns = ["_build"]
source_suffix = ".rst"
master_doc = "index"

# Sphinx options
language = "en"

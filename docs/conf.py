import os

# Add dev disclaimer.
_release = {}
exec(
    compile(open("../voila/_version.py").read(), "../voila/_version.py", "exec"),
    _release,
)
if _release["version_info"][-1] == "dev":
    rst_prolog = """
    .. note::

        This documentation is for a development version of Voilà. There may be
        significant differences from the latest stable release.

    """

on_rtd = os.environ.get("READTHEDOCS", None) == "True"

html_theme = "pydata_sphinx_theme"
html_theme_options = {"github_url": "https://github.com/voila-dashboards/voila"}


extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.intersphinx",
    "sphinx.ext.napoleon",
    "sphinxcontrib.video",
    "myst_parser",
]

source_suffix = ".md"
master_doc = "index"
project = "voila"
copyright = "2020, The Voilà Development Team"
author = "The Voilà Development Team"
version = ".".join(map(str, _release["version_info"][:2]))
release = _release["__version__"]
language = "en"

html_logo = "voila-logo.svg"

exclude_patterns = []
highlight_language = "python"
pygments_style = "sphinx"
todo_include_todos = False
htmlhelp_basename = "voiladoc"

intersphinx_mapping = {"python": ("https://docs.python.org", None)}

myst_heading_anchors = 3

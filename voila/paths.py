#############################################################################
# Copyright (c) 2018, Voila Contributors                                    #
#                                                                           #
# Distributed under the terms of the BSD 3-Clause License.                  #
#                                                                           #
# The full license is in the file LICENSE, distributed with this software.  #
#############################################################################

import os

from jupyter_core.paths import jupyter_path

ROOT = os.path.dirname(__file__)
STATIC_ROOT = os.path.join(ROOT, 'static')
# if the directory above us contains the following paths, it means we are installed in dev mode (pip install -e .)
DEV_MODE = os.path.exists(os.path.join(ROOT, '../setup.py')) and os.path.exists(os.path.join(ROOT, '../share'))

notebook_path_regex = r'(.*\.ipynb)'


def collect_template_paths(
        nbconvert_template_paths,
        static_paths,
        tornado_template_paths):
    """
    Voila supports custom templates for rendering notebooks.

    For a specified template name, `collect_template_paths` collects
        - nbconvert template paths,
        - static paths,
        - tornado template paths,
    by looking in the standard Jupyter data directories (PREFIX/share/jupyter/voila/templates)
    with different prefix values (user directory, sys prefix, and then system prefix) which
    allows users to override templates locally.

    The function will recursively load the base templates upon which the specified template
    may be based.
    """

    # We look at the usual jupyter locations, and for development purposes also
    # relative to the package directory (first entry, meaning with highest precedence)
    search_directories = []
    if DEV_MODE:
        search_directories.append(os.path.abspath(os.path.join(ROOT, '..', 'share', 'jupyter', 'voila', 'templates')))
    search_directories.extend(jupyter_path('voila', 'templates'))

    for search_directory in search_directories:
        if not os.path.exists(search_directory):
            continue

        for template_name in os.listdir(search_directory):
            template_directory = os.path.join(search_directory, template_name)

            extra_nbconvert_path = os.path.join(template_directory, 'nbconvert_templates')
            nbconvert_template_paths.insert(0, extra_nbconvert_path)

            extra_static_path = os.path.join(template_directory, 'static')
            static_paths.insert(0, extra_static_path)

            extra_template_path = os.path.join(template_directory, 'templates')
            tornado_template_paths.insert(0, extra_template_path)

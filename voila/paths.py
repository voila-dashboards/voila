#############################################################################
# Copyright (c) 2018, Voila Contributors                                    #
#                                                                           #
# Distributed under the terms of the BSD 3-Clause License.                  #
#                                                                           #
# The full license is in the file LICENSE, distributed with this software.  #
#############################################################################

import os
import json

from jupyter_core.paths import jupyter_path

ROOT = os.path.dirname(__file__)
STATIC_ROOT = os.path.join(ROOT, 'static')
# if the directory above us contains the following paths, it means we are installed in dev mode (pip install -e .)
DEV_MODE = os.path.exists(os.path.join(ROOT, '../setup.py')) and os.path.exists(os.path.join(ROOT, '../share'))

notebook_path_regex = r'(.*\.ipynb)'


def collect_template_paths(
        nbconvert_template_paths,
        static_paths,
        tornado_template_paths,
        template_name='default'):
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

    found_at_least_one = False
    for search_directory in search_directories:
        template_directory = os.path.join(search_directory, template_name)
        if os.path.exists(template_directory):
            found_at_least_one = True
            conf = {}
            conf_file = os.path.join(template_directory, 'conf.json')
            if os.path.exists(conf_file):
                with open(conf_file) as f:
                    conf = json.load(f)

            # For templates that are not named 'default', we assume the default base_template is 'default'
            # that means that even the default template could have a base_template when explicitly given.
            if template_name != 'default' or 'base_template' in conf:
                collect_template_paths(
                    nbconvert_template_paths,
                    static_paths,
                    tornado_template_paths,
                    conf.get('base_template', 'default'))

            extra_nbconvert_path = os.path.join(template_directory, 'nbconvert_templates')
            nbconvert_template_paths.insert(0, extra_nbconvert_path)

            extra_static_path = os.path.join(template_directory, 'static')
            static_paths.insert(0, extra_static_path)

            extra_template_path = os.path.join(template_directory, 'templates')
            tornado_template_paths.insert(0, extra_template_path)

            # We don't look at multiple directories, once a directory with a given name is found at a
            # given level of precedence (for instance user directory), we don't look further (for instance
            # in sys.prefix)
            break
    if not found_at_least_one:
        paths = "\n\t".join(search_directories)
        raise ValueError('No template sub-directory with name %r found in the following paths:\n\t%s' % (template_name, paths))

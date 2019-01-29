#############################################################################
# Copyright (c) 2018, Voila Contributors                                    #
#                                                                           #
# Distributed under the terms of the BSD 3-Clause License.                  #
#                                                                           #
# The full license is in the file LICENSE, distributed with this software.  #
#############################################################################

import os
from jupyter_core.paths import jupyter_path
import json

ROOT = os.path.dirname(__file__)
STATIC_ROOT = os.path.join(ROOT, 'static')

def collect_template_paths(config,
       nbconvert_template_paths,
       static_paths,
       template_paths,
       template_name='default'):
    # we look at the usual jupyter locations, and for development purposes also
    # relative to the package directory (with highest precedence)
    template_directories = \
        [os.path.abspath(os.path.join(ROOT, '..', 'share', 'jupyter', 'voila', 'template', template_name))] +\
        jupyter_path('voila', 'template', template_name)

    for dirname in template_directories:
        if os.path.exists(dirname):
            config_current = {}
            conf_file = os.path.join(dirname, 'conf.json')
            if os.path.exists(conf_file):
                with open(conf_file) as f:
                    config_current = json.load(f)

            # For templates that are not named 'default', we assume the default base_template is 'default'
            # that means that even the default template could have a base_template when explicitly given.
            if template_name != 'default' or 'base_template' in config_current:
                collect_template_paths(
                    config,
                    nbconvert_template_paths,
                    static_paths,
                    template_paths,
                    config_current.get('base_template', 'default'))
                config.update(config_current)

            extra_nbconvert_path = os.path.join(dirname, 'nbconvert_templates')
            #if not os.path.exists(extra_nbconvert_path):
            #    log.warning('template named %s found at path %r, but %s does not exist', template_name,
            #                dirname, extra_nbconvert_path)
            nbconvert_template_paths.insert(0, extra_nbconvert_path)

            extra_static_path = os.path.join(dirname, 'static')
            #if not os.path.exists(extra_static_path):
            #    log.warning('template named %s found at path %r, but %s does not exist', template_name,
            #                dirname, extra_static_path)
            static_paths.insert(0, extra_static_path)

            extra_template_path = os.path.join(dirname, 'templates')
            #if not os.path.exists(extra_template_path):
            #    log.warning('template named %s found at path %r, but %s does not exist', template_name,
            #                dirname, extra_template_path)
            template_paths.insert(0, extra_template_path)

            # We don't look at multiple directories, once a directory with a given name is found at a
            # given level of precedence (for instance user directory), we don't look further (for instance
            # in sys.prefix)
            break

    return nbconvert_template_paths, static_paths, template_paths

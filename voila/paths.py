#############################################################################
# Copyright (c) 2018, Voilà Contributors                                    #
# Copyright (c) 2018, QuantStack                                            #
#                                                                           #
# Distributed under the terms of the BSD 3-Clause License.                  #
#                                                                           #
# The full license is in the file LICENSE, distributed with this software.  #
#############################################################################

import os
import json
from pathlib import Path
import shutil

from jupyter_core.paths import jupyter_path
import nbconvert.exporters.templateexporter


ROOT = os.path.dirname(__file__)
STATIC_ROOT = os.path.join(ROOT, 'static')
# if the directory above us contains the following paths, it means we are installed in dev mode (pip install -e .)
DEV_MODE = os.path.exists(os.path.join(ROOT, '../setup.py')) and os.path.exists(os.path.join(ROOT, '../share'))


def collect_template_paths(app_names, template_name='default', prune=False, root_dirs=None):
    return collect_paths(app_names, template_name, include_root_paths=True, prune=prune, root_dirs=root_dirs)


def collect_static_paths(app_names, template_name='default', prune=False, root_dirs=None):
    return collect_paths(
        app_names, template_name, include_root_paths=False, prune=prune, root_dirs=root_dirs, subdir='static'
    )


def collect_paths(
    app_names, template_name='default', subdir=None, include_root_paths=True, prune=False, root_dirs=None
):
    """
    Voilà supports custom templates for rendering notebooks.
    For a specified template name, `collect_paths` can be used to collects
        - template paths
        - resources paths (by using the subdir arg)

    by looking in the standard Jupyter data directories:
    $PREFIX/share/jupyter/templates/<app_name>/<template_name>[/subdir]
    with different prefix values (user directory, sys prefix, and then system prefix) which
    allows users to override templates locally.
    The function will recursively load the base templates upon which the specified template
    may be based.
    """
    found_at_least_one = False
    paths = []
    full_paths = []  # only used for error reporting

    root_dirs = root_dirs or _default_root_dirs()

    # first find a list of the template 'hierarchy'
    template_names = _find_template_hierarchy(app_names, template_name, root_dirs)

    # the order of the loop determines the precedense of the template system
    # * first template_names, e.g. if we inherit from default template, we only
    #   want to find those files last
    for template_name in template_names:
        for root_dir in root_dirs:
            for app_name in app_names:
                app_dir = os.path.join(root_dir, app_name, 'templates')
                path = os.path.join(app_dir, template_name)
                if subdir:
                    path = os.path.join(path, subdir)
                if not prune or os.path.exists(path):
                    paths.append(path)
                    found_at_least_one = True
            # for app_name in app_names:
            #     app_dir = os.path.join(root_dir, app_name, 'templates')
            #     # we include app_dir for when we want to be explicit, but less than root_dir, e.g.
            #     # {% extends 'classic/base.html' %}
            #     paths.append(app_dir)
            #     full_paths.append(app_dir)  # only used for error msg
    if include_root_paths:
        for root_dir in root_dirs:
            # we include root_dir for when we want to be very explicit, e.g.
            # {% extends 'nbconvert/templates/classic/base.html' %}
            paths.append(root_dir)
            for app_name in app_names:
                app_dir = os.path.join(root_dir, app_name, 'templates')
                # we include app_dir for when we want to be explicit, but less than root_dir, e.g.
                # {% extends 'classic/base.html' %}
                paths.append(app_dir)

    if not found_at_least_one:
        paths = "\n\t".join(full_paths)
        raise ValueError(
            'No template sub-directory with name %r found in the following paths:\n\t%s' % (template_name, paths)
        )
    return paths


def _default_root_dirs(root_first=True):
    # We look at the usual jupyter locations, and for development purposes also
    # relative to the package directory (first entry, meaning with highest precedence)
    root_dirs = []
    pkg_share_jupyter = os.path.abspath(os.path.join(ROOT, '..', 'share', 'jupyter'))
    if DEV_MODE and root_first:
        root_dirs.append(pkg_share_jupyter)
    if nbconvert.exporters.templateexporter.DEV_MODE:
        root_dirs.append(os.path.abspath(os.path.join(nbconvert.exporters.templateexporter.ROOT, '..', '..', 'share', 'jupyter')))

    root_dirs.extend(jupyter_path())

    if DEV_MODE and not root_first:
        root_dirs.append(pkg_share_jupyter)

    return root_dirs


def _find_template_hierarchy(app_names, template_name, root_dirs):
    template_names = []
    while template_name is not None:
        template_names.append(template_name)
        conf = {}
        for root_dir in root_dirs:
            for app_name in app_names:
                conf_file = os.path.join(root_dir, app_name, 'templates', template_name, 'conf.json')
                if os.path.exists(conf_file):
                    with open(conf_file) as f:
                        new_conf = json.load(f)
                        new_conf.update(conf)
                        conf = new_conf
        if 'base_template' in conf:
            template_name = conf['base_template']
        else:
            if template_name == 'base':
                # the default template has no base_template
                template_name = None
            else:
                # if not specified, 'base' is assumed
                template_name = 'base'
    return template_names


def get_existing_template_dirs(app_names, template_name, root_first=False):
    """
    Return a list of available template directories with
    template name ``template_name``. ``app_names`` might be
    ``["nbconvert", "voila"]``, for example. If ``root_first``,
    give priority to the current working directory in the search
    for a ``share`` directory which will be the destination
    for custom templates. If False, set lowest priority to the cwd.
    """
    return [
        d for d in collect_paths(
            app_names,
            template_name,
            # only use a ``share`` dir in the cwd as a last resort:
            root_dirs=_default_root_dirs(root_first=root_first)
        )
        if os.path.exists(d) and template_name in d
    ]


def install_custom_template(
    share_path,
    template_name,
    reference_template_name='base',
    try_symlink=True,
    overwrite=False,
    include_root_paths=False
):
    """
    Make a custom template available for use with Voilà.

    Generate copies of/symbolic links pointing towards custom template files,
    which will be located in directories where Voilà expects them. By default,
    the template will be copied/symlinked where the Voilà template named "base"
    can be found on your machine.

    Parameters
    ----------
    share_path : path-like, str
        Path to a ``share`` directory containing the custom template to be
        installed. Custom templates will be organized in the subdirs:
        ``share/jupyter/nbconvert/templates/<template_name>`` and
        ``share/jupyter/voila/templates/<template_name>``.
    template_name : str
        Name of the custom template
    reference_template_name : str (default is "base")
        Name of a default Voilà template. This function will try to install the
        custom template in the same location as this reference template.
    try_symlink : bool
        If True, try to make a symlink and fall back on making a copy. Otherwise,
        make a copy.
    overwrite : bool
        Overwrite custom template directories with the same name if they
        already exist.
    include_root_paths : bool
        If True, include the cwd in the search for the ``share`` directory
        which will become the destination path for the custom template
        directories.
    """
    # search for existing custom template and "base" (default) template paths
    # that may already be installed on this machine:
    app_names = ['nbconvert', 'voila']
    custom_template_dirs = get_existing_template_dirs(
        app_names, template_name, include_root_paths=include_root_paths
    )
    reference_template_dirs = get_existing_template_dirs(
        app_names, reference_template_name, include_root_paths=include_root_paths
    )

    # if there are existing jdaviz template dirs but overwrite=False, raise error:
    if not overwrite and len(custom_template_dirs):
        raise FileExistsError(
            f"Existing files found at {custom_template_dirs} which "
            f"would be overwritten, but overwrite=False."
        )

    prefix_targets = [
        os.path.join(app_name, "templates") for app_name in app_names
    ]

    if len(reference_template_dirs):
        target_dir = Path(reference_template_dirs[0]).absolute().parents[2]
    else:
        raise FileNotFoundError(f"No {reference_template_name} template found for voila.")

    for prefix_target in prefix_targets:
        # Path to the source for the custom template to be installed
        source = os.path.join(share_path, 'share', 'jupyter', prefix_target, template_name)
        parent_dir_of_target = os.path.join(target_dir, prefix_target)
        # Path to destination for new custom template
        target = os.path.join(parent_dir_of_target, template_name)
        abs_source = os.path.abspath(source)
        try:
            rel_source = os.path.relpath(abs_source, parent_dir_of_target)
        except Exception:
            # relpath does not work if source/target on different Windows disks.
            try_symlink = False

        try:
            os.remove(target)
        except Exception:
            try:
                shutil.rmtree(target)  # Maybe not a symlink
            except Exception:
                pass

        # Cannot symlink without relpath or Windows admin priv in some OS versions.
        try:
            if try_symlink:
                print('making symlink:', rel_source, '->', target)
                os.symlink(rel_source, target)
            else:
                raise OSError('just make copies')
        except Exception:
            print('making copy:', abs_source, '->', target)
            shutil.copytree(abs_source, target)

#############################################################################
# Copyright (c) 2018, Voilà Contributors                                    #
# Copyright (c) 2018, QuantStack                                            #
#                                                                           #
# Distributed under the terms of the BSD 3-Clause License.                  #
#                                                                           #
# The full license is in the file LICENSE, distributed with this software.  #
#############################################################################
from pathlib import Path
from jupyter_packaging.setupbase import ensure_targets

import setuptools

HERE = Path(__file__).parent.resolve()

# The name of the project
NAME = "voila"

labext_name = "@voila-dashboards/jupyterlab-preview"
lab_extension_dest = HERE / NAME / "labextension"

# Representative files that should exist after a successful build
ensured_targets = [
    str(HERE / "share/jupyter/voila/templates/base/static/voila.js"),
    str(lab_extension_dest / "package.json"),
]


data_files_spec = [
    (
        "etc/jupyter/jupyter_server_config.d",
        "etc/jupyter/jupyter_server_config.d",
        "voila.json",
    ),
    (
        "etc/jupyter/jupyter_notebook_config.d",
        "etc/jupyter/jupyter_notebook_config.d",
        "voila.json",
    ),
    (
        "etc/jupyter/nbconfig/notebook.d",
        "etc/jupyter/nbconfig/notebook.d",
        "voila.json",
    ),
    ("share/jupyter/nbextensions/voila", "voila/static", "extension.js"),
    ("share/jupyter/labextensions/%s" % labext_name, str(lab_extension_dest), "**"),
    ("share/jupyter/labextensions/%s" % labext_name, str(HERE), "install.json"),
    ("share/jupyter/voila/templates", "share/jupyter/voila/templates", "**/*[!.map]"),
]

try:
    from jupyter_packaging import wrap_installers, npm_builder, get_data_files

    # In develop mode, just run yarn
    builder = npm_builder(build_cmd="build", npm="jlpm", force=True)
    cmdclass = wrap_installers(post_develop=builder, ensured_targets=ensured_targets)

    setup_args = dict(cmdclass=cmdclass, data_files=get_data_files(data_files_spec))
except ImportError:
    setup_args = dict()


if __name__ == "__main__":
    setuptools.setup(**setup_args)

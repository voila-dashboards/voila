#############################################################################
# Copyright (c) 2018, Voilà Contributors                                    #
# Copyright (c) 2018, QuantStack                                            #
#                                                                           #
# Distributed under the terms of the BSD 3-Clause License.                  #
#                                                                           #
# The full license is in the file LICENSE, distributed with this software.  #
#############################################################################
from pathlib import Path
from urllib.request import urlopen
import setuptools
import sys
import os

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


jupyterlab_apputils_version = "3.2.8"
jupyterlab_theme_light_version = "3.2.8"

css_files = [
    (
        "https://unpkg.com/@jupyterlab/apputils@%s/style/materialcolors.css"
        % jupyterlab_apputils_version,
        "materialcolors.css",
    ),
    (
        "https://unpkg.com/@jupyterlab/theme-light-extension@%s/style/variables.css"
        % jupyterlab_theme_light_version,
        "labvariables.css",
    ),
]


class FetchCSS(setuptools.Command):
    """Fetch CSS files from the CDNs."""

    description = "Fetch CSS from CDN"
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        for template_name in ["classic", "reveal"]:
            for url, filename in css_files:
                directory = os.path.join(
                    "share", "jupyter", "voila", "templates", template_name, "static"
                )
                dest = os.path.join(directory, filename)
                if not os.path.exists(directory):
                    os.makedirs(directory)
                if not os.path.exists(".git") and os.path.exists(dest):
                    # not running from git, nothing to do
                    return
                print("Downloading CSS: %s" % url)
                try:
                    css = urlopen(url).read()
                except Exception as e:
                    msg = "Failed to download css from %s: %s" % (url, e)
                    print(msg, file=sys.stderr)

                    if os.path.exists(dest):
                        print("Already have CSS: %s, moving on." % dest)
                    else:
                        raise OSError("Need CSS to proceed.")
                    return

                with open(dest, "wb") as f:
                    f.write(css)
                print("Downloaded Notebook CSS to %s" % dest)


def download_css_first(command):
    class CSSFirst(command):
        def run(self):
            self.distribution.run_command("download_css")
            return command.run(self)

    return CSSFirst


try:
    from jupyter_packaging import wrap_installers, npm_builder, get_data_files

    # In develop mode, just run yarn
    builder = npm_builder(build_cmd="build", npm="jlpm", force=True)
    cmdclass = wrap_installers(post_develop=builder, ensured_targets=ensured_targets)

    cmdclass["download_css"] = FetchCSS
    cmdclass["develop"] = download_css_first(cmdclass["develop"])
    cmdclass["sdist"] = download_css_first(cmdclass["sdist"])
    cmdclass["bdist_wheel"] = download_css_first(cmdclass["bdist_wheel"])

    setup_args = dict(cmdclass=cmdclass, data_files=get_data_files(data_files_spec))
except ImportError:
    setup_args = dict()


if __name__ == "__main__":
    setuptools.setup(**setup_args)

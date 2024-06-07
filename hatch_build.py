import os
import sys
from urllib.request import urlopen

from hatchling.builders.hooks.plugin.interface import BuildHookInterface

JUPYTERLAB_APPUTILS_VERSION = "3.2.8"
JUPYTERLAB_THEME_LIGHT_VERSION = "3.2.8"

CSS_FILES = [
    (
        f"https://unpkg.com/@jupyterlab/apputils@{JUPYTERLAB_APPUTILS_VERSION}/style/materialcolors.css",
        "materialcolors.css",
    ),
    (
        f"https://unpkg.com/@jupyterlab/theme-light-extension@{JUPYTERLAB_THEME_LIGHT_VERSION}/style/variables.css",
        "labvariables.css",
    ),
]


class CustomBuildHook(BuildHookInterface):
    def initialize(self, version, build_data):
        for url, filename in CSS_FILES:
            directory = os.path.join(
                "share", "jupyter", "voila", "templates", "base", "static"
            )
            dest = os.path.join(directory, filename)
            if not os.path.exists(directory):
                os.makedirs(directory)
            if not os.path.exists(".git") and os.path.exists(dest):
                # not running from git, nothing to do
                return
            print(f"Downloading CSS: {url}")
            try:
                css = urlopen(url).read()
            except Exception as e:
                msg = f"Failed to download css from {url}: {e}"
                print(msg, file=sys.stderr)

                if os.path.exists(dest):
                    print(f"Already have CSS: {dest}, moving on.")
                else:
                    raise OSError("Need CSS to proceed.")
                return

            with open(dest, "wb") as f:
                f.write(css)
            print(f"Downloaded Notebook CSS to {dest}")

import os

from jupyter_packaging import (
    create_cmdclass,
    install_npm,
    ensure_targets,
    get_version,
    combine_commands,
    skip_if_exists,
)
import setuptools

HERE = os.path.abspath(os.path.dirname(__file__))

# The name of the project
name = "voila"

# Get our version
version = get_version(os.path.join(name, "_version.py"))

labext_name = "@voila-dashboards/jupyterlab-preview"
lab_extension_dest = os.path.join(HERE, name, "labextension")
lab_extension_source = os.path.join(HERE, "packages", "jupyterlab-preview")
voila_js_source = os.path.join(HERE, "packages", "voila")

# Representative files that should exist after a successful build
jstargets = [
    os.path.join(HERE, "share", "jupyter", "voila", "templates", "base", "static", "voila.js"),
    os.path.join(lab_extension_dest, "package.json"),
]

package_data_spec = {name: ["*"]}


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
    ("share/jupyter/labextensions/%s" % labext_name, lab_extension_dest, "**"),
    ("share/jupyter/labextensions/%s" % labext_name, HERE, "install.json"),
    ("share/jupyter/voila/templates", "share/jupyter/voila/templates", "**"),
]


cmdclass = create_cmdclass(
    "jsdeps", package_data_spec=package_data_spec, data_files_spec=data_files_spec
)

js_command = combine_commands(
    install_npm(voila_js_source, build_cmd="build", npm=["npm"]),
    install_npm(lab_extension_source, build_cmd="build:prod", npm=["jlpm"]),
    ensure_targets(jstargets),
)

is_repo = os.path.exists(os.path.join(HERE, ".git"))
if is_repo:
    cmdclass["jsdeps"] = js_command
else:
    cmdclass["jsdeps"] = skip_if_exists(jstargets, js_command)


with open("README.md", "r") as fh:
    long_description = fh.read()

setup_args = dict(
    name=name,
    version=version,
    url="https://github.com/voila-dashboards/voila",
    author="Voila Development Team",
    author_email="jupyter@googlegroups.com",
    description="Voilà turns Jupyter notebooks into standalone web applications",
    long_description=long_description,
    long_description_content_type="text/markdown",
    cmdclass=cmdclass,
    packages=setuptools.find_packages(),
    entry_points={"console_scripts": ["voila = voila.app:main"]},
    install_requires=[
        "jupyter_server>=0.3.0,<2.0.0",
        "jupyter_client>=6.1.3,<7",
        "nbclient>=0.4.0,<0.6",
        "nbconvert>=6.0.0,<7",
    ],
    extras_require={
        "test": [
            "ipywidgets",
            "mock",
            # TODO: unpin
            "jupyter_server~=1.0.1",
            "matplotlib",
            "pytest",
            "pytest-tornasync",
        ]
    },
    zip_safe=False,
    include_package_data=True,
    python_requires=">=3.6",
    license="BSD-3-Clause",
    platforms="Linux, Mac OS X, Windows",
    keywords=["Jupyter", "JupyterLab", "Voila"],
    classifiers=[
        "License :: OSI Approved :: BSD License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Framework :: Jupyter",
    ],
)


if __name__ == "__main__":
    setuptools.setup(**setup_args)

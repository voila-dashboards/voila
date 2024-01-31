% Copyright (c) 2018, Voilà Contributors
% Copyright (c) 2018, QuantStack
%
% Distributed under the terms of the BSD 3-Clause License.
%
% The full license is in the file LICENSE, distributed with this software.

(contribute)=

# Contributing to Voilà

Voilà is a subproject of Project Jupyter and subject to the [Jupyter governance](https://github.com/jupyter/governance) and [Code of conduct](https://github.com/jupyter/governance/blob/master/conduct/code_of_conduct.md).

## General Guidelines

For general documentation about contributing to Jupyter projects, see the [Project Jupyter Contributor Documentation](https://jupyter.readthedocs.io/en/latest/contributing/content-contributor.html).

## Community

The Voilà team organizes public video meetings. The schedule for future meetings and minutes of past meetings can be found on our [team compass](https://voila-dashboards.github.io/)

## Setting up a development environment

First, you need to fork the project. Then setup your environment:

```bash
# create a new conda environment
conda create -n voila -c conda-forge notebook jupyterlab nodejs "yarn<4" pip
conda activate voila

# download voila from your GitHub fork
git clone https://github.com/<your-github-username>/voila.git

# install JS dependencies and build js assets
cd voila
yarn install

# install Voilà in editable mode
python -m pip install -e .
```

## Run Voilà

To start Voilà, run:

```bash
voila
```

or

```bash
python -m voila
```

This will open a new browser tab at \[<http://localhost:8866/](http://localhost:8866/>).

When making changes to the frontend side of Voilà, open a new terminal window and run:

```bash
cd packages/voila/
npm run watch
```

Then reload the browser tab.

**Note**: the notebooks directory contains some examples that can be run with Voilà.
Checkout the [instructions](project:using.md#the-example-notebooks) in the user guide
for details on how to run them.

## Extensions

### Server extension

To manually enable the classic notebook server extension:

```bash
jupyter serverextension enable voila --sys-prefix
```

For Jupyter Server:

```bash
jupyter server extension enable voila.server_extension --sys-prefix
```

This makes Voilà available as a server extension: [http://localhost:8888/voila/tree](http://localhost:8888/voila/tree).

### Notebook extension

To install the notebook extension:

```bash
jupyter nbextension install voila --sys-prefix --py
jupyter nbextension enable voila --sys-prefix --py
```

### JupyterLab extension

Node.js is required and can be installed with conda:

```bash
conda install -c conda-forge nodejs
```

The JupyterLab extension requires the server extension to be enabled. This can be done by running:

```bash
jupyter serverextension enable voila --sys-prefix
```

You can verify if the server extension is enabled by running:

```bash
jupyter serverextension list
```

If you use Jupyter Server:

```bash
jupyter server extension enable voila --sys-prefix
```

You can verify if the server extension is enabled by running:

```bash
jupyter server extension list
```

The JupyterLab extension is developed as a prebuilt extension using the new distribution system
added in JupyterLab 3.0. To setup the development environment:

```bash
# install the package in development mode
python -m pip install -e .

# link your development version of the extension with JupyterLab
jupyter labextension develop . --overwrite

# build the lab extension
jlpm run build --scope @voila-dashboards/jupyterlab-preview

# it is also possible to start in watch mode to pick up changes automatically
jlpm run watch
```

### Frontend Packages

The Voilà repository consists of several packages such as the Voilà frontend and the JupyterLab extension.

It follows a monorepo structure and uses `lerna` to streamline the workflow.

To build all the frontend packages at once, run the following commands:

```bash
# install dependencies
jlpm

# build the packages
jlpm run build
```

This will run the `build` script in each of the packages.

Using this structure, packages can easily be linted and follow the same code style and conventions used in other Jupyter projects.
To lint the packages:

```bash
# install dependencies
jlpm

# run ESLint
jlpm run eslint

# run prettier
jlpm run prettier
```

## About the Voila Frontend

The Voila frontend is built as a JupyterLab-based application using JupyterLab components.

This makes it possible to reuse existing plugins and extensions for Jupyterlab such as core JupyterLab plugins like the JSON viewer,
as well as third-party mime renderers like the [FASTA viewer](https://github.com/jupyterlab/jupyter-renderers).

The Voila frontend is able to load existing JupyterLab extensions installed as prebuilt extensions under `${PREFIX}/share/labextensions`,
similar to the way it works in JupyterLab.

These extensions are typically distributed via `pip` and `conda` packages and can easily be installed by end users without requiring Node.js.
Widget packages usually now include a prebuilt extension for JupyterLab 3.0 by default, which should automatically work in Voila too.

Check out the [JupyterLab Documentation on prebuilt extensions](https://jupyterlab.readthedocs.io/en/stable/extension/extension_dev.html#prebuilt-extensions) for more info.

The code for the frontend is located under `packages/voila`, with support for loading federated extensions in `packages/voila/index.js`.

## Tests

Install the test dependencies

```bash
python -m pip install -e ".[test]"
```

Enable the Jupyter server extension:

```bash
jupyter server extension enable voila.server_extension --sys-prefix
```

Running the tests locally also requires the `test_template` and `skip_template` to be installed:

```bash
python -m pip install ./tests/test_template ./tests/skip_template
```

Finally, to run the tests:

```bash
python -m pytest
```

## Editing templates

The default template files are located in the folder `share/jupyter/voila/templates/default`. They are automatically picked up when running Voilà in development mode.

After editing the templates, reload the browser tab to see the changes.

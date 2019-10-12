# Contributing to voila

## Setting up a development environment

First, you need to fork the project. Then setup your environment:

```bash
# create a new conda environment
conda create -n voila -c conda-forge notebook nodejs
conda activate voila

# download voila from your GitHub fork
git clone https://github.com/<your-github-username>/voila.git

# install JS dependencies and build js assets
cd voila/js
npm install
cd ..

# install voila in editable mode
python -m pip install -e .
```

## Run voila

To start voila, run:

```bash
voila
```

or

```bash
python -m voila
```

This will open a new browser tab at [http://localhost:8866/](http://localhost:8866/).

When making changes to the frontend side of voila, open a new terminal window and run:

```bash
cd js/
npm run watch
```

Then reload the browser tab.

## Extensions

### Server extension

To manually enable the classic notebook server extension:

```bash
jupyter serverextension enable voila --sys-prefix
```

For Jupyter Server:

```bash
jupyter extension enable voila --sys-prefix
```

This makes voila available as a server extension: [http://localhost:8888/voila/tree](http://localhost:8888/voila/tree).

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

To install the JupyterLab extension locally:

```bash
jupyter labextension install @jupyter-widgets/jupyterlab-manager
jupyter labextension install ./packages/jupyterlab-voila

# start in watch mode to pick up changes automatically
jupyter lab --watch
```

## Running the examples

A few additional libraries can be installed to run the example notebooks:

```bash
conda install -c conda-forge ipywidgets ipyvolume bqplot scipy
```

The examples can then be served with:

```bash
cd notebooks/
voila
```

## Tests

Install the test dependencies

```bash
python -m pip install -e ".[test]"
```

Enable the Jupyter server extension:

```bash
jupyter extension enable voila --sys-prefix
```

Running the tests locally also requires the `test_template` to be installed:

```bash
python -m pip install ./tests/test_template
```

Finally, to run the tests:

```bash
python -m pytest
```


## Editing templates

The default templates are located in the following folder: [share/jupyter/voila/templates/default](./share/jupyter/voila/templates/default). They are automatically picked up when running voila in development mode.

Alternatively, there is a Voila template cookiecutter available to give you a running start. [Link](https://github.com/aartgoossens/voila-template-cookiecutter).
This cookiecutter contains some docker configuration for live reloading of your template changes to make development easier.

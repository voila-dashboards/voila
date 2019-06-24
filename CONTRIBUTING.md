# Contributing to voila

## Setting up a development environment

```bash
# create a new conda environment
conda create -n voila -c conda-forge notebook nodejs
conda activate voila

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
jupyter nbextension install voila --sys-prefix
jupyter nbextension enable voila --sys-prefix
```

### JupyterLab extension

Node.js is required and can be installed with conda:

```bash
conda install -c conda-forge nodejs
```

The extension is being developed for JupyterLab 1.0, which is going to be [released very soon](https://github.com/jupyterlab/jupyterlab/issues/6504). To install the alpha 1.0 release:

```bash
pip install --pre jupyterlab
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

After editing the templates, reload the browser tab to see the changes.

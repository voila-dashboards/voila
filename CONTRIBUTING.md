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

To manually enable the classic notebook server extension:

```bash
jupyter serverextension enable voila --sys-prefix [--py | --user]
```

For Jupyter Server:

```bash
jupyter extension enable voila --sys-prefix [--py | --user]
```

This makes voila available as a server extension: [http://localhost:8888/voila/tree](http://localhost:8888/voila/tree).

To install the notebook extension:

```bash
jupyter nbextension install voila --sys-prefix [--py | --user]
jupyter nbextension enable voila --sys-prefix [--py | --user]
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

To run the tests:

```bash
python -m pip install ".[test]"
python -m pytest
```

## Editing templates

The default templates are located in the following folder: [share/jupyter/voila/templates/default](./share/jupyter/voila/templates/default). They are automatically picked up when running voila in development mode.

After editing the templates, reload the browser tab to see the changes.

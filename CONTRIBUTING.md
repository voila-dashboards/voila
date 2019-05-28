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

## Editing templates

The default templates are located in the following folder: [share/jupyter/voila/templates/default](./share/jupyter/voila/templates/default). They are automatically picked up when running voila in development mode.

After editing the templates, reload the browser tab to see the changes.

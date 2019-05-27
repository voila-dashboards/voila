# Contributing to Voila

## Setting up a development environment

```bash
# create a new conda environment
conda create -n voila -c conda-forge notebook nodejs
conda activate voila

# install voila in editable mode
python -m pip install -e .
```

When making changes to the frontend side of voila, open a new terminal window and run:

```bash
cd js/
npm run watch
```

## Running the examples

A few additional libraries can be installed to run the example notebooks:

```bash
# to run the examples
conda install -c conda-forge ipywidgets bqplot
```

The examples can then be served with:

```bash
cd notebooks/
voila
```
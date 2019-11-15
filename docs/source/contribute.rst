.. Copyright (c) 2018, Voila Contributors
   Copyright (c) 2018, QuantStack
   
   Distributed under the terms of the BSD 3-Clause License.
   
   The full license is in the file LICENSE, distributed with this software.

.. _install:

=====================
Contributing to Voilà
=====================

Voilà is a subproject of Project Jupyter and subject to the `Jupyter governance <https://github.com/jupyter/governance>`_ and `Code of conduct <https://github.com/jupyter/governance/blob/master/conduct/code_of_conduct.md>`_.

General Guidelines
==================

For general documentation about contributing to Jupyter projects, see the `Project Jupyter Contributor Documentation <https://jupyter.readthedocs.io/en/latest/contributor/content-contributor.html>`_.

Community
=========

The Voilà team organizes public video meetings. The schedule for future meetings and minutes of past meetings can be found on our `team compass <https://voila-dashboards.github.io/>`_

Setting up a development environment
====================================

First, you need to fork the project. Then setup your environment:

.. code-block:: bash

   # create a new conda environment
   conda create -n voila -c conda-forge notebook nodejs
   conda activate voila

   # download voila from your GitHub fork
   git clone https://github.com/<your-github-username>/voila.git

   # install JS dependencies and build js assets
   cd voila/js
   npm install
   cd ..

   # install Voila in editable mode
   python -m pip install -e .

Run Voilà
=========

To start Voilà, run:

.. code-block:: bash

   voila

or

.. code-block:: bash

   python -m voila

This will open a new browser tab at [http://localhost:8866/](http://localhost:8866/).

When making changes to the frontend side of Voilà, open a new terminal window and run:

.. code-block:: bash

   cd js/
   npm run watch

Then reload the browser tab.

Extensions
==========

Server extension
----------------

To manually enable the classic notebook server extension:

.. code-block:: bash

   jupyter serverextension enable voila --sys-prefix

For Jupyter Server:

.. code-block:: bash

   jupyter extension enable voila --sys-prefix

This makes Voilà available as a server extension: `http://localhost:8888/voila/tree <http://localhost:8888/voila/tree>`_.

Notebook extension
------------------

To install the notebook extension:

.. code-block:: bash

   jupyter nbextension install voila --sys-prefix --py
   jupyter nbextension enable voila --sys-prefix --py

JupyterLab extension
--------------------

Node.js is required and can be installed with conda:

.. code-block:: bash

   conda install -c conda-forge nodejs

The JupyterLab extension requires the server extension to be enabled. This can be done by running:

.. code-block:: bash

   jupyter serverextension enable voila --sys-prefix

You can verify if the server extension is enabled by running:

.. code-block:: bash

   jupyter serverextension list

To install the JupyterLab extension locally:

.. code-block:: bash

   jupyter labextension install @jupyter-widgets/jupyterlab-manager
   jupyter labextension install ./packages/jupyterlab-voila
   
   # start in watch mode to pick up changes automatically
   jupyter lab --watch

Running the examples
====================

A few additional libraries can be installed to run the example notebooks:

.. code-block:: bash

   conda install -c conda-forge ipywidgets ipyvolume bqplot scipy

The examples can then be served with:

.. code-block:: bash

   cd notebooks/
   voila

Tests
=====

Install the test dependencies

.. code-block:: bash

   python -m pip install -e ".[test]"

Enable the Jupyter server extension:

.. code-block:: bash

   jupyter extension enable voila --sys-prefix

Running the tests locally also requires the `test_template` to be installed:

.. code-block:: bash

   python -m pip install ./tests/test_template

Finally, to run the tests:

.. code-block:: bash

   python -m pytest

Editing templates
=================

The default template files are located in the folder `share/jupyter/voila/templates/default`. They are automatically picked up when running Voilà in development mode.

After editing the templates, reload the browser tab to see the changes.


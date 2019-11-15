.. Copyright (c) 2018, Voila Contributors
   Copyright (c) 2018, QuantStack
   
   Distributed under the terms of the BSD 3-Clause License.
   
   The full license is in the file LICENSE, distributed with this software.

.. _using:

===========
Using Voilà
===========

Voilà can be used as a standalone application, or as a Jupyter server
extension. This page describes how to do each. Before you begin, make
sure that you follow the steps in :ref:`install`.

The following sections cover how to use Voilà.

As a standalone application
===========================

Voilà can be used to run, convert, and serve a Jupyter notebook as a
standalone app. This can be done via the command-line, with the following
pattern:

.. code-block:: bash

   voila <path-to-notebook> <options>

For example, to render the ``bqplot`` example notebook as a standalone app, run

.. code-block:: bash

   git clone https://github.com/QuantStack/voila
   cd voila
   voila notebooks/bqplot.ipynb

Voilà displays a message when your notebook-based application is live.
By default, Voilà runs at ``localhost:8866``.

To serve a **directory of Jupyter Notebooks**, navigate to the directory
you'd like to serve, then simply run ``voila``:

.. code-block:: bash

   cd notebooks/
   voila

The page served by Voilà will now contain a list of any notebooks in the
directory. By clicking on one, you will trigger Voilà's conversion process.
A new Jupyter kernel will be created for each notebook you click.

As a Jupyter server extension
=============================

You can also use Voilà from within a Jupyter server (e.g., after running
``jupyter lab`` or ``jupyter notebook``).

.. note::

   Voilà can also be used as a notebook server extension, both with the
   `notebook <https://github.com/jupyter/notebook>`_ server or with the
   `jupyter_server <https://github.com/jupyter/jupyter_server>`_.

To use Voilà within a pre-existing Jupyter server, first start the server,
then go to the following URL:

.. code-block:: bash

   <url-of-my-server>/voila

For example, if you typed ``jupyter lab`` and it was running at
``http://localhost:8888/lab``, then Voilà would be accessed at
``http://localhost:8888/voila``.

In this case, Voilà will serve the directory in which the Jupyter
server was started.

How does Voilà work?
====================

When Voilà is run on a notebook, the following steps occur:

#. Voilà runs the code in the notebook and collects the outputs
#. The notebook and its outputs are converted to HTML. By default,
   the notebook **code cells are hidden**.
#. This page is served either as a Tornado application, or via the
   Jupyter server.
#. When users access the page, the widgets on the page have access to
   the underlying Jupyter kernel.

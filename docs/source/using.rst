.. _using:

===========
Using Voila
===========

Voila can be used as a standalone application, or as a Jupyter server
extension. This page describes how to do each. Before you begin, make
sure that you follow the steps in :ref:`install`.

The following sections cover how to use Voila.

As a standalone application
===========================

Voila can be used to run, convert, and serve a Jupyter notebook as a
standalone app. This can be done via the command-line, with the following
pattern:

.. code-block:: bash

   voila <path-to-notebook> <options>

For example, to render the ``bqplot`` example notebook as a standalone app, run

.. code-block:: bash

   git clone https://github.com/QuantStack/voila
   cd voila
   voila notebooks/bqplot.ipynb

Voila display a message when your notebook-based application is live.
By default, Voila runs at ``localhost:8866``.

To serve a **directory of Jupyter Notebooks**, navigate to the directory
you'd like to serve, then simply run ``voila``:

.. code-block:: bash

   cd notebooks/
   voila

The page served by Voila will now contain a list of any notebooks in the
directory. By clicking on one, you will trigger Voila's conversion process.
A new Jupyter kernel will be created for each notebook you click.

As a Jupyter server extension
=============================

You can also use Voila from within a Jupyter server (e.g., after running
``jupyter lab`` or ``jupyter notebook``).

.. note::

   Voila can also be used as a notebook server extension, both with the
   `notebook <https://github.com/jupyter/notebook>`_ server or with the
   `jupyter_server <https://github.com/jupyter/jupyter_server>`_.

To use Voila within a pre-existing Jupyter server, first start the server,
then go to the following URL:

.. code-block:: bash

   <url-of-my-server>/voila

For example, if you typed ``jupyter lab`` and it was running at
``http://localhost:8888/lab``, then Voila would be accessed at
``http://localhost:8888/voila``.

In this case, Voila will serve the directory in which the Jupyter
server was started.

How does Voila work?
====================

When Voila is run on a notebook, the following steps occur:

#. Voila runs the code in the notebook and collects the outputs
#. The notebook and its outputs are converted to HTML. By default,
   the notebook **code cells are hidden**.
#. This page is served either as a Tornado application, or via the
   Jupyter server.
#. When users access the page, the widgets on the page have access to
   the underlying Jupyter kernel.
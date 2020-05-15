.. Copyright (c) 2018, Voila Contributors
   Copyright (c) 2018, QuantStack

   Distributed under the terms of the BSD 3-Clause License.

   The full license is in the file LICENSE, distributed with this software.

.. _customize:

=================
Customizing Voilà
=================

There are many ways you can customize Voilà to control the look and feel
of the dashboards you create.

Controlling the nbconvert template
==================================

Voilà uses **nbconvert** to convert your Jupyter Notebook into an HTML dashboard.
nbconvert has a rich templating system that allows you to customize the way in
which your Jupyter Notebook is converted into HTML.

By default, Voilà will render the HTML from your notebook in the same linear fashion
that the notebook follows. If you'd like to use a different layout, this can be
controlled by creating a new nbconvert template, registering it with Voilà,
and calling it from the command-line like so:

.. code-block:: bash

   voila <path-to-notebook> --template=<name-of-template>

For example, Voilà includes one other template that uses a Javascript library and
an alternate ``<div>`` layout in order to let the user drag and drop cells.

For example, to use the `gridstack <https://github.com/voila-dashboards/voila-gridstack/>`_ template, use the command:

.. code-block:: bash

   voila <path-to-notebook> --template=gridstack

Creating your own template
==========================

You can create your own nbconvert template for use with Voilà. This allows you
to control the look and feel of your dashboard.

In order to create your own template, first familiarize yourself with **Jinja**,
**HTML**, and **CSS**. Each of these is used in creating custom templates.
For more information, see
`the nbconvert templates documentation <https://nbconvert.readthedocs.io/en/latest/customizing.html#Custom-Templates>`_.
For one example, `check out the nbconvert basic HTML template <https://github.com/jupyter/nbconvert/blob/master/nbconvert/templates/html/basic.tpl>`_.

Where are Voilà templates located?
----------------------------------

All Voilà templates are stored as folders with particular configuration/template files inside.
These folders can exist in the standard Jupyter configuration locations, in a folder called ``voila/templates``.
For example:

.. code-block:: bash

   ~/.local/share/jupyter/voila/templates
   ~/path/to/env/dev/share/jupyter/voila/templates
   /usr/local/share/jupyter/voila/templates
   /usr/share/jupyter/voila/templates

Voilà will search these locations for a folder, one per template, where
the folder name defines the template name.

The Voilà template structure
----------------------------

Within each template folder, you can provide your own nbconvert templates, static
files, and HTML templates (for pages such as a 404 error). For example, here is
the folder structure of the base Voilà template (called "default"):

.. code-block:: bash

    tree path/to/env/share/jupyter/voila/templates/default/
    ├── nbconvert_templates
    │   ├── base.tpl
    │   └── voila.tpl
    └── templates
        ├── 404.html
        ├── error.html
        ├── page.html
        └── tree.html

**To customize the nbconvert template**, store it in a folder called ``templatename/nbconvert_templates/voila.tpl``.
In the case of the default template, we also provide a ``base.tpl`` that our custom template uses as a base.
The name ``voila.tpl`` is special - you cannot name your custom nbconvert something else.

**To customize the HTML page templates**, store them in a folder called ``templatename/templates/<name>.html``.
These are files that Voilà can serve as standalone HTML (for example, the ``tree.html`` template defines how
folders/files are displayed in ``localhost:8866/voila/tree``). You can override the defaults by providing your
own HTML files of the same name.

**To configure your Voilà template**, you should add a ``config.json`` file to the root of your template
folder.

.. todo: Add information on config.json


An example custom template
--------------------------

To show how to create your own custom template, let's create our own nbconvert template.
We'll have two goals:

1. Add an ``<h1>>`` header displaying "Our awesome template" to the Voilà dashboard.
2. Add a custom 404.html page that displays an image.

First, we'll create a folder in ``~/.local/share/jupyter/voila/templates`` called ``mytemplate``::

    mkdir ~/.local/share/jupyter/voila/templates/mytemplate
    cd ~/.local/share/jupyter/voila/templates/mytemplate

Next, we'll copy over the base template files for Voilà, which we'll modify::

    cp -r path/to/env/share/jupyter/voila/templates/default/nbconvert_templates ./
    cp -r path/to/env/share/jupyter/voila/templates/default/templates ./

We should now have a folder structure like this::

    tree .
    ├── nbconvert_templates
    │   ├── base.tpl
    │   └── voila.tpl
    └── templates
        ├── 404.html
        ├── error.html
        ├── page.html
        └── tree.html

Now, we'll edit ``nbconvert_templates/voila.tpl`` to include a custom H1 header.

As well as ``templates/tree.html`` to include an image.

Finally, we can tell Voilà to use this custom template the next time we use it on
a Jupyter notebook by using the name of the folder in the ``--template`` parameter::

    voila mynotebook.ipynb --template=mytemplate


The result should be a Voilà dashboard with your custom modifications made!

Voila template cookiecutter
-----------------------------
There is a Voila template cookiecutter available to give you a running start.
This cookiecutter contains some docker configuration for live reloading of your template changes to make development easier.
Please refer to the `cookiecutter repo <https://github.com/voila-dashboards/voila-template-cookiecutter>`_ for more information on how to use the Voila template cookiecutter.


Adding your own static files
============================

If you create your own theme, you may also want to define and use your
own static files, such as CSS and Javascript. To use your own static files,
follow these steps:

1. Create a folder along with your template (e.g., ``mytemplate/static/``).
2. Put your static files in this template.
3. In your template file (e.g. ``voila.tpl``), link these static files with
   the following path::

      {{resources.base_url}}voila/static/<path-to-static-files>

4. When you call ``voila``, configure the static folder by using the
   ``--static`` kwarg, or by configuring ``--VoilaConfiguration.static_root``.

Any folders / files that are inside the folder given with this configuration
will be copied to ``{{resources.base_url}}voila/static/``.

For example, if you had a CSS file called ``custom.css`` in ``static/css``,
you would link it in your template like so::

   <link rel="stylesheet" type="text/css" href="{{resources.base_url}}voila/static/css/custom.css"></link>


Configure Voilà for the Jupyter Server
======================================

Several pieces of ``voila``'s functionality can be controlled when it is
run. This can be done either as a part of the standalone CLI, or with the
Jupyter Server. To configure ``voila`` when run by the Jupyter Server,
use the following pattern when invoking the command that runs Jupyter (e.g.,
Jupyter Lab or Jupyter Notebook)::

   <jupyter-command> --VoilaConfiguration.<config-key>=<config-value>

For example, to control the template used by ``voila`` from within a Jupyter
Lab session, use the following command when starting the server::

   jupyter lab --VoilaConfiguration.template=distill

When users run ``voila`` by hitting the ``voila/`` endpoint, this configuration
will be used.

Serving static files
====================

Unlike JupyterLab or the classic notebook server, ``voila`` does not serve
all files that are present in the directory of the notebook. Only files that
match one of the whitelists and none of the blacklist regular expression are
served by Voilà::

    voila mydir --VoilaConfiguration.file_whitelist="['.*']" \
      --VoilaConfiguration.file_blacklist="['private.*', '.*\.(ipynb)']"

Which will serve all files, except anything starting with private, or notebook files::

   voila mydir --VoilaConfiguration.file_whitelist="['.*\.(png|jpg|gif|svg|mp4|avi|ogg)']"

Will serve many media files, and also never serve notebook files (which is the default blacklist).

Run scripts
===========

Voilà can run text (or script) files, by configuring how a file extension maps to a kernel language::

   voila mydir --VoilaConfiguration.extension_language_mapping='{".py": "python", ".jl": "julia"}'

Voilà will find a kernel that matches the language specified, but can also be
configured to use a specific kernel for each language::

   voila mydir --VoilaConfiguration.extension_language_mapping='{".py": "python", ".jl": "julia"}'\
     --VoilaConfiguration.language_kernel_mapping='{"python": "xpython"}'

In this case it will use the `xeus-python
<https://github.com/QuantStack/xeus-python/>`_. kernel to run `.py` files.

Note that the script will be executed as notebook with a single cell, meaning
that only the last expression will be printed as output. Use the Jupyter
display mechanism to output any text or rich output such as Jupyter widgets. For
Python this would be a call to `IPython.display.display`.

Using `Jupytext <https://github.com/mwouts/jupytext>`_ is another way to support
script files. After installing jupytext, Voilà will see script files as if they
are notebooks, and requires no extra configuration.

Cull idle kernels
=================

Voilà starts a new Jupyter kernel every time a notebook is rendered to the user. In some situations, this can lead to a higher memory consumption.

The Jupyter Server exposes several options that can be used to terminate kernels that are not active anymore. They can be configured using the Voilà standalone app:

.. code-block:: bash

   voila --MappingKernelManager.cull_interval=60 --MappingKernelManager.cull_idle_timeout=120

The server will periodically check for idle kernels, in this example every 60 seconds, and cull them if they have been idle for more than 120 seconds.

The same parameters apply when using Voilà as a server extension:

.. code-block:: bash

    jupyter notebook --MappingKernelManager.cull_interval=60 --MappingKernelManager.cull_idle_timeout=120

There is also the ``MappingKernelManager.cull_busy`` and ``MappingKernelManager.cull_connected`` options to cull busy kernels and kernels with an active connection.

For more information about these options, check out the `Jupyter Server <https://jupyter-server.readthedocs.io/en/latest/config.html#options>`_ documentation.
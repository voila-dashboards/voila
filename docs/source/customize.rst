.. _customize:

=================
Customizing Voila
=================

There are many ways you can customize Voila to control the look and feel
of the dashboards you create.

Controlling the nbconvert template
==================================

Voila uses **nbconvert** to convert your Jupyter Notebook into an HTML dashboard.
nbconvert has a rich templating system that allows you to customize the way in
which your Jupyter Notebook is converted into HTML.

By default, Voila will render the HTML from your notebook in the same linear fashion
that the notebook follows. If you'd like to use a different layout, this can be
controlled by creating a new nbconvert template, registering it with Voila,
and calling it from the command-line like so:

.. code-block:: bash

   voila <path-to-notebook> --template=<name-of-template>

For example, Voila includes one other template that uses a Javascript library and
an alternate ``<div>`` layout in order to let the user drag and drop cells.

To use this template when creating your dashboard, use the following command:

.. code-block:: bash

   voila <path-to-notebook> --template=gridstack

Creating your own template
==========================

You can create your own nbconvert template for use with Voila. This allows you
to control the look and feel of your dashboard.

In order to create your own template, first familiarize yourself with **Jinja**,
**HTML**, and **CSS**. Each of these is used in creating custom templates.
For more information, see
`the nbconvert templates documentation <https://nbconvert.readthedocs.io/en/latest/customizing.html#Custom-Templates>`_.
For one example, `check out the nbconvert basic HTML template <https://github.com/jupyter/nbconvert/blob/master/nbconvert/templates/html/basic.tpl>`_.

Where are Voila templates located?
----------------------------------

All voila templates are stored as folders with particular configuration/template files inside.
These folders can exist in the standard Jupyter configuration locations, in a folder called ``voila/template``.
For example:

.. code-block:: bash

   ~/.local/share/jupyter/voila/template
   ~/path/to/env/dev/share/jupyter/voila/template
   /usr/local/share/jupyter/voila/template
   /usr/share/jupyter/voila/template

Voila will search these locations for a folder, one per template, where
the folder name defines the template name.

The Voila template structure
----------------------------

Within each template folder, you can provide your own nbconvert templates, static
files, and HTML templates (for pages such as a 404 error). For example, here is
the folder structure of the base Voila template (called "default"):

.. code-block:: bash

    tree path/to/env/share/jupyter/voila/template/default/
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

**To customize the HTML page templates**, store them i na folder called ``templatename/templates/<name>.html``.
These are files that Voila can serve as standalone HTML (for example, the ``tree.html`` template defines how
folders/files are displayed in ``localhost:8866/voila/tree``). You can override the defaults by providing your
own HTML files of the same name.

**To configure your Voila template**, you should add a ``config.json`` file to the root of your template
folder.

.. todo: Add information on config.json


An example custom template
--------------------------

To show how to create your own custom template, let's create our own nbconvert template.
We'll have two goals:

1. Add an ``<h1>>`` header displaying "Our awesome template" to the voila dashboard.
2. Add a custom 404.html page that displays an image.

First, we'll create a folder in ``~/.local/share/jupyter/voila/template`` called ``mytemplate``::

    mkdir ~/.local/share/jupyter/voila/template/mytemplate
    cd ~/.local/share/jupyter/voila/template/mytemplate

Next, we'll copy over the base template files for voila, which we'll modify::

    cp -r path/to/env/share/jupyter/voila/template/default/nbconvert_templates ./
    cp -r path/to/env/share/jupyter/voila/template/default/templates ./

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

Finally, we can tell ``Voila`` to use this custom template the next time we use it on
a Jupyter notebook by using the name of the folder in the ``--template`` parameter::

voila mynotebook.ipynb --template=mytemplate

The result should be a Voila dashboard with your custom modifications made!

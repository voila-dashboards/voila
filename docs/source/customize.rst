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

Creating and registering a template
-----------------------------------

You can create your own nbconvert template for use with Voila. This allows you
to control the look and feel of your dashboard.

In order to create your own template, first familiarize yourself with **Jinja**,
**HTML**, and **CSS**. Each of these is used in creating custom templates.
For more information, see
`the nbconvert templates documentation <https://nbconvert.readthedocs.io/en/latest/customizing.html#Custom-Templates>`_.
For one example, `check out the nbconvert basic HTML template <https://github.com/jupyter/nbconvert/blob/master/nbconvert/templates/html/basic.tpl>`_.

Once you've created your custom template, you can make register it with
Voila by

.. todo: add information for how to register a template


Adding custom CSS and Javascript
================================

You can also add the location of any static files (CSS, JavaScript, and extra HTML)
with the ``--static`` parameter. These files will be available to be used from your template.
For example, if you have some custom CSS in a folder called ``my_css``, use the following
command to include it in rendering your dashboard:

.. code-block:: bash

   voila <path-to-notebook> --template=<path-to-template.tpl> --static=my_css

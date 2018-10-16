Voila
=====

[![Binder](https://img.shields.io/badge/launch-binder-brightgreen.svg)](https://mybinder.org/v2/gh/QuantStack/voila/stable?urlpath=voila/tree/notebooks)

Rendering of live Jupyter notebooks with interactive widgets.

Introduction
------------

Voila serves live Jupyter notebook including Jupyter interactive widgets.

Unlike the usual HTML-converted notebooks, each user connecting to the Voila
tornado application gets a dedicated Jupyter kernel which can execute the
callbacks to changes in Jupyter interactive widgets.

- By default, voila disallows execute requests from the front-end, disabling
  the ability to execute arbitrary code.
- By defaults, voila runs with the `strip_source` option, which strips out the
  input cells from the rendered notebook.

When using these default settings, the code powering the Jupyter notebook is
never sent to the front-end.

Usage
-----

To render the `bqplot` example notebook as a Voila app, run

```
voila bqplot.ipynb
```

Related projects
----------------

Voila depends on the [nbconvert](https://github.com/jupyter/nbconvert) and
[jupyter_server](https://github.com/jupyter/jupyter_server/).

License
-------

We use a shared copyright model that enables all contributors to maintain the
copyright on their contributions.

This software is licensed under the BSD-3-Clause license. See the
[LICENSE](LICENSE) file for details.


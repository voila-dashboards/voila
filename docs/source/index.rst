Voila
=====

Voila renders Jupyter notebooks in a read-only fashion, including live
interactive widgets.

Unlike the usual HTML-converted notebooks, each user connected to Voila gets a
dedicated Jupyter kernel which can execute the callbacks to changes in Jupyter
interactive widgets.

By default, voila disallows execute requests from the front-end, disabling the
ability to execute arbitrary code. By defaults, voila runs with the
`strip_source` option set to `True`, which strips out the input cells from the
rendered notebook.

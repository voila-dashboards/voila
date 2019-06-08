# ![voila](docs/source/voila.svg)

[![Documentation](http://readthedocs.org/projects/voila/badge/?version=latest)](https://voila.readthedocs.io/en/latest/?badge=latest)
[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/QuantStack/voila/stable?urlpath=voila%2Ftree%2Fnotebooks)
[![Join the Gitter Chat](https://badges.gitter.im/Join%20Chat.svg)](https://gitter.im/QuantStack/Lobby?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)

Rendering of live Jupyter notebooks with interactive widgets.

## Introduction

Voila serves live Jupyter notebook including Jupyter interactive widgets.

Unlike the usual HTML-converted notebooks, each user connecting to the Voila
tornado application gets a dedicated Jupyter kernel which can execute the
callbacks to changes in Jupyter interactive widgets.

- By default, voila disallows execute requests from the front-end, preventing
  execution of arbitrary code.
- By defaults, voila runs with the `strip_source` option, which strips out the
  input cells from the rendered notebook.

## Installation

Voila can be installed with the conda package manager

```
conda install -c conda-forge voila
```

or from pypi

```
pip install voila
```

## Usage

### As a standalone tornado application

To render the `bqplot` example notebook as a standalone app, run

```
voila bqplot.ipynb
```

To serve a directory of jupyter notebooks, just run `voila` with no argument.

For more command line options (e.g., to specify an alternate port number),
run `voila --help`.

### As a server extension to `notebook` or `jupyter_server`

Voila can also be used as a notebook server extension, both with the
[notebook](https://github.com/jupyter/notebook) server or with
[jupyter_server](https://github.com/jupyter/jupyter_server).

To install the notebook server extension, run

```
jupyter serverextension enable voila --sys-prefix
```

When running the notebook server, the voila app is accessible from the base url
suffixed with `voila`.

## Examples

The following two examples show how a standalone Jupyter notebook can be turned into a separate app, from the command-line integration.

**Rendering a notebook including interactive widgets and rich mime-type rendering.**
![voila basics](voila-basics.gif)

**Rendering a notebook making use of a custom widget library ([bqplot](https://github.com/bloomberg/bqplot)).**

![voila bqplot](voila-bqplot.gif)

The sources of the Jupyter notebook can be displayed in a voila app if option `strip_sources` is set to `False`.

**Showing the source code for a voila notebook.**

![voila sources](voila-sources.gif)

## Related projects

Voila depends on the [nbconvert](https://github.com/jupyter/nbconvert) and
[jupyter_server](https://github.com/jupyter/jupyter_server/).

## License

We use a shared copyright model that enables all contributors to maintain the
copyright on their contributions.

This software is licensed under the BSD-3-Clause license. See the
[LICENSE](LICENSE) file for details.

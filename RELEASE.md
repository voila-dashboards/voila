# Making a new release of Voilà

## Using `jupyter_releaser`

The recommended way to make a release is to use [`jupyter_releaser`](https://github.com/jupyter-server/jupyter_releaser#typical-workflow).

This repository contains the two workflows located under https://github.com/voila-dashboards/voila/actions:

- Step 1: Prep Release
- Step 2: Publish Release

## Bumping versions

`voila` follows a similar bump strategy as in JupyterLab:

https://github.com/jupyterlab/jupyterlab/blob/master/RELEASE.md#bump-version

`jupyter_releaser` handles the bump automatically so it is not necessary to do it manually, as long as the spec is correctly specified in the workflow.

### Manual bump

To manually bump the version, run:

```bash
# install the dependencies
python -m pip install -e ".[test,dev]"

# bump the version
python scripts/bump-version.py <spec>
```

Where `<spec>` can be one of the following: `patch`, `minor`, `major`, `release` or `next` (auto for `patch` or `minor`).

## Major JS bump

When there is a breaking change in a JS package, the version of the package should be bumped by one major version.

For example if the version of the preview extension was `2.1.0-alpha.1` and a breaking is introduced, bump to `3.0.0-alpha.0`.

## Releasing on conda-forge

1. Open a new PR on https://github.com/conda-forge/voila-feedstock to update the `version` and the `sha256` hash (see [example](https://github.com/conda-forge/voila-feedstock/pull/23/files))
2. Wait for the tests
3. Merge the PR

The new version will be available on `conda-forge` soon after.

### Making a new release of @voila-dashboards/jupyterlab-preview

The prebuilt extension is already packaged in the main Python package.

However we also publish it to `npm` to:

- let other third-party extensions depend on `@voila-dashboards/jupyterlab-preview`
- let users install from source if they would like to

# Making a new release of Voilà

## Using `jupyter_releaser`

The recommended way to make a release is to use [`jupyter_releaser`](https://github.com/jupyter-server/jupyter_releaser#typical-workflow).

## Bumping versions

`voila` follows a similar bump strategy as in JupyterLab:

https://github.com/jupyterlab/jupyterlab/blob/master/RELEASE.md#bump-version

`jupyter_releaser` handles the bump automatically so it is not necessary to do it manually, as long as the spec is correctly specified in the workflow.

### Manual bump

To manually bump the version, run:

```bash
# install the dependencies
python -m pip install -r requirements-test.txt
python -m pip install -e .

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

## Manual Release Process

### Getting a clean environment

Creating a new environment can help avoid pushing local changes and any extra tag.

```bash
mamba create -q -y -n voila-release -c conda-forge twine nodejs keyring pip matplotlib tornado jupyter-packaging jupyterlab build
conda activate voila-release
```

Alternatively, the local repository can be cleaned with:

```bash
git clean -fdx
```

### Releasing on PyPI

Make sure the `dist/` folder is empty.

1. Bump the version:
   - `python -m pip install bump2version jupyter-releaser`
   - For a patch or build release: `python scripts/bump-version next`
2. `python -m build`
3. Double check the size of the bundles in the `dist/` folder
4. Make sure the JupyterLab extension is correctly bundled in source distribution
5. Run the tests
   - `pip install "dist/voila-X.Y.Z-py3-none-any.whl[test]`
   - `cd tests/test_template`
   - `pip install tests/test_template tests/skip_template`
   - `py.test`
6. `export TWINE_USERNAME=mypypi_username`
7. `twine upload dist/*`

### Committing and tagging

Commit the changes, create a new release tag, and update the `stable` branch (for Binder), where `x.y.z` denotes the new version:

```bash
git checkout main
git add voila/_version.py
git commit -m "Release x.y.z"
git tag x.y.z
git checkout stable
git reset --hard main
git push origin main stable x.y.z
```

### Making a new release of @voila-dashboards/jupyterlab-preview

The prebuilt extension is already packaged in the main Python package.

However we also publish it to `npm` to:

- let other third-party extensions depend on `@voila-dashboards/jupyterlab-preview`
- let users install from source if they would like to

### Releasing on npm

1. Update [packages/jupyterlab-preview/package.json](./packages/jupyterlab-preview/package.json) with the new version number (to be done when making a new release of the Python package)
2. `cd ./packages/jupyterlab-preview`
3. `npm login`
4. `npm publish`

### Committing

The JupyterLab extension should follow the publish cycle of the main Python package (see above).

# Making a new release of Voilà

## Automated releases

Releases are automated using GitHub Actions. They are triggered when a new tag is pushed to the remote.

To cut a new release, run the following:

```bash
# checkout the master branch
git checkout master

# bump the version
# 1. update `voila/_version.py`
# 2. update `environment.yml`

# commit and push
git add voila/_version.py environment.yml
git commit -m "Release x.y.z"
git tag x.y.z
git checkout stable
git reset --hard master
git push origin master stable x.y.z
```

The release workflow also creates a GitHub release with the new changes generated with [github-changelog-generator](https://github.com/github-changelog-generator/github-changelog-generator).

If you would still like to do the release manually instead, read below.

## Manual Releases

### Getting a clean environment

Creating a new environment can help avoid pushing local changes and any extra tag.

```bash
mamba create -q -y -n voila-release -c conda-forge twine nodejs keyring pip matplotlib tornado jupyter-packaging jupyterlab
conda activate voila-release
```

Alternatively, the local repository can be cleaned with:

```bash
git clean -fdx
```

### Releasing on PyPI

Make sure the `dist/` folder is empty.

1. Update [voila/\_version.py](./voila/_version.py) and [environment.yml](./environment.yml) with the new version number (see and [example diff](https://github.com/voila-dashboards/voila/commit/5c6fd8dd3ea71412ae9c20c25248453d22a3b60a))
2. `python setup.py sdist bdist_wheel`
3. Double check the size of the bundles in the `dist/` folder
4. If the JupyterLab extension has changed, make sure to bump the version number in `./packages/jupyterlab-preview/package.json`
5. Make sure the JupyterLab extension is correctly bundled in source distribution
6. Run the tests
   - (pip install "dist/voila-X.Y.Z-py3-none-any.whl[test]" && (cd tests/test_template; pip install .) && (cd tests/skip_template; pip install .) && py.test)
7. `export TWINE_USERNAME=mypypi_username`
8. `twine upload dist/*`

### Releasing on conda-forge

1. Open a new PR on https://github.com/conda-forge/voila-feedstock to update the `version` and the `sha256` hash (see [example](https://github.com/conda-forge/voila-feedstock/pull/23/files))
2. Wait for the tests
3. Merge the PR

The new version will be available on `conda-forge` soon after.

### Committing and tagging

Commit the changes, create a new release tag, and update the `stable` branch (for Binder), where `x.y.z` denotes the new version:

```bash
git checkout master
git add voila/_version.py environment.yml
git commit -m "Release x.y.z"
git tag x.y.z
git checkout stable
git reset --hard master
git push origin master stable x.y.z
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

# Making a new release of Voilà

## Getting a clean environment

Creating a new environment can help avoid pushing local changes and any extra tag.

```bash
mamba create -q -y -n voila-release -c conda-forge twine nodejs keyring pip matplotlib tornado
conda activate voila-release
```

Alternatively, the local repository can be cleaned with:

```bash
git clean -fdx
```

## Releasing on PyPI

Make sure the `dist/` folder is empty.

1. Update [voila/_version.py](./voila/_version.py) and [environment.yml](./environment.yml) with the new version number (see and [example diff](https://github.com/voila-dashboards/voila/commit/5c6fd8dd3ea71412ae9c20c25248453d22a3b60a))
2. `python setup.py sdist bdist_wheel`
3. Double check the size of the bundles in the `dist/` folder
4. Run the tests
   * (pip install "dist/voila-X.Y.Z-py3-none-any.whl[test]" && (cd tests/test_template; pip install .) && (cd tests/skip_template; pip install .) && py.test)
5. `export TWINE_USERNAME=mypypi_username`
6. `twine upload dist/*`

## Releasing on conda-forge

1. Open a new PR on https://github.com/conda-forge/voila-feedstock to update the `version` and the `sha256` hash (see [example](https://github.com/conda-forge/voila-feedstock/pull/23/files))
2. Wait for the tests
3. Merge the PR

The new version will be available on `conda-forge` soon after.

## Committing and tagging

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

# Making a new release of @jupyter-voila/jupyterlab-preview

## Releasing on npm

1. Update [packages/jupyterlab-voila/package.json](./packages/jupyterlab-voila/package.json) with the new version number
2. `cd ./packages/jupyterlab-voila`
3. `npm login`
4. `npm publish`

## Committing

Commit and push the changes, where `x.y.z` denotes the new version:

```bash
git add ./packages/jupyterlab-voila/package.json
git commit -m "Release @jupyter-voila/jupyterlab-preview x.y.z"
git push origin master
```

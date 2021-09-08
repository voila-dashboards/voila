# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.import click

# Heavily inspired by:
# - https://github.com/jupyterlab/jupyterlab/blob/master/buildutils/src/bumpversion.ts
# - https://github.com/jupyterlab/retrolab/blob/main/buildutils/src/release-bump.ts

import click
from jupyter_releaser.util import run


OPTIONS = ["major", "minor", "release", "build"]


def get_python_version():
    """Return the version of the voila Python package"""
    import voila

    return voila.__version__


def patch():
    python_version = get_python_version()
    if "a" in python_version or "b" in python_version or "rc" in python_version:
        raise Exception("Can only make a patch release from a final version")

    run("bumpversion patch", quiet=True)
    # switches to alpha
    run("bumpversion release --allow-dirty", quiet=True)
    # switches to beta
    run("bumpversion release --allow-dirty", quiet=True)
    # switches to rc.
    run("bumpversion release --allow-dirty", quiet=True)
    # switches to final.


def update(spec, force=False):
    prev = get_python_version()

    # Make sure we have a valid version spec.
    if spec not in OPTIONS:
        raise Exception(f"Version spec must be one of: {OPTIONS}")

    is_final = "a" not in prev and "b" not in prev and "c" not in prev

    if is_final and spec == "release":
        raise Exception('Use "major" or "minor" to switch back to alpha release')

    if is_final and spec == "build":
        raise Exception("Cannot increment a build on a final release")

    # TODO: check git status

    # If this is a major release during the alpha cycle, bump
    # just the Python version.
    if "a" in prev and spec == "major":
        run(f"bumpversion {spec}")
        return

    # Determine the version spec to use for lerna.
    lerna_version = "preminor"
    if spec == "build":
        lerna_version = "prerelease"
    # a -> b
    elif spec == "release" and "a" in prev:
        lerna_version = "prerelease --preid=beta"
    # b -> rc
    elif spec == "release" and "b" in prev:
        lerna_version = "prerelease --preid=rc"
    # rc -> final
    elif spec == "release" and "c" in prev:
        lerna_version = "patch"
    if lerna_version == "preminor":
        lerna_version += " --preid=alpha"

    cmd = f"jlpm run lerna version --force-publish --no-push --no-git-tag-version {lerna_version}"
    if force:
        cmd += " --yes"

    # For a preminor release, we bump 10 minor versions so that we do
    # not conflict with versions during minor releases of the top level package.
    if lerna_version == "preminor":
        for i in range(10):
            run(cmd)
    else:
        run(cmd)

    # Bump the version.
    run(f"bumpversion {spec} --allow-dirty")


@click.command()
@click.argument("spec", nargs=1)
@click.option("--force", default=False)
def bump(spec, force):
    if spec == "patch":
        patch()
        return

    update(spec, force)


if __name__ == "__main__":
    bump()

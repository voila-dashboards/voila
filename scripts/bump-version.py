# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.import click

# Heavily inspired by:
# - https://github.com/jupyterlab/jupyterlab/blob/master/buildutils/src/bumpversion.ts
# - https://github.com/jupyterlab/retrolab/blob/main/buildutils/src/release-bump.ts

import click
from jupyter_releaser.util import is_prerelease, get_version, run


OPTIONS = ["major", "minor", "release", "build", "patch", "next"]


def patch(force=False):
    version = get_version()
    if is_prerelease(version):
        raise Exception("Can only make a patch release from a final version")

    run("hatch version patch", quiet=True)

    # Version the changed
    cmd = "jlpm && jlpm run lerna version patch --no-push --force-publish --no-git-tag-version"
    if force:
        cmd += " --yes"
    run(cmd)


def update(spec, force=False):
    prev = get_version()

    is_final = not is_prerelease(prev)

    if is_final and spec == "build":
        raise Exception("Cannot increment a build on a final release")

    # If this is a major release during the alpha cycle, bump
    # just the Python version.
    if "a" in prev and spec == "major":
        run(f"hatch version {spec}")
        return

    # Determine the version spec to use for lerna and hatch
    py_spec = spec
    lerna_version = "preminor"
    if spec == "build":
        lerna_version = "prerelease"
        if 'a' in prev:
            py_spec = 'a'
        elif 'b' in prev:
            py_spec = 'b'
        elif 'rc' in prev:
            py_spec = 'rc'
    # a -> b
    elif spec == "release" and "a" in prev:
        lerna_version = "prerelease --preid=beta"
        py_spec = 'beta'
    # b -> rc
    elif spec == "release" and "b" in prev:
        lerna_version = "prerelease --preid=rc"
        py_spec = 'rc'
    # rc -> final
    elif spec == "release" and "c" in prev:
        lerna_version = "patch"
        py_spec = 'release'
    elif spec == "release":
        py_spec = 'minor,alpha'

    if lerna_version == "preminor":
        lerna_version += " --preid=alpha"

    cmd = f"jlpm && jlpm run lerna version --force-publish --no-push --no-git-tag-version {lerna_version}"
    if force:
        cmd += " --yes"

    # For a preminor release, we bump 10 minor versions so that we do
    # not conflict with versions during minor releases of the top level package.
    if lerna_version == "preminor":
        for i in range(10):
            run(cmd)
    else:
        run(cmd)

    # Bump the Python version
    run(f"hatch version {py_spec}")


@click.command()
@click.option("--force", default=False, is_flag=True)
@click.argument("spec", nargs=1)
def bump(force, spec):
    status = run("git status --porcelain").strip()
    if len(status) > 0:
        raise Exception("Must be in a clean git state with no untracked files")

    # Make sure we have a valid version spec.
    if spec not in OPTIONS:
        raise ValueError(f"Version spec must be one of: {OPTIONS}")

    prev = get_version()
    is_final = not is_prerelease(prev)
    if spec == "next":
        spec = "patch" if is_final else "build"

    if spec == "patch":
        patch(force)
        return

    update(spec, force)


if __name__ == "__main__":
    bump()

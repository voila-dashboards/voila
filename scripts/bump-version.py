import click
from jupyter_releaser.util import run


def get_python_version():
    """Return the version of the voila Python package"""
    import voila

    return voila.__version__


@click.command()
@click.option("--spec", default="patch", help="Number of greetings.")
def bump(spec):
    python_version = get_python_version()
    print(python_version)
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


if __name__ == "__main__":
    bump()

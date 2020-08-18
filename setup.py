from setuptools import setup, find_packages, Command
from setuptools.command.sdist import sdist
from setuptools.command.build_py import build_py
from setuptools.command.develop import develop
from setuptools.command.egg_info import egg_info
from setuptools.command.bdist_egg import bdist_egg

from subprocess import check_call, CalledProcessError

import os
import shlex
import sys
import shutil

from distutils import log

log.set_verbosity(log.DEBUG)

here = os.path.dirname(os.path.abspath(__file__))
node_root = os.path.join(here, 'js')
is_repo = os.path.exists(os.path.join(here, '.git'))


def in_read_the_docs():
    return os.environ.get('READTHEDOCS') == 'True'


def js_first(command, strict=False):
    """decorator for building minified js/css prior to another command"""

    class DecoratedCommand(command):
        def run(self):
            jsdeps = self.distribution.get_command_obj('jsdeps')
            if not is_repo and all(os.path.exists(t) for t in jsdeps.targets):
                # sdist, nothing to do
                command.run(self)
                return

            try:
                self.distribution.run_command('jsdeps')
            except Exception as e:
                missing = [t for t in jsdeps.targets if not os.path.exists(t)]
                if strict or missing:
                    log.warn('rebuilding js and css failed')
                    if missing:
                        log.error('missing files: %s' % missing)
                    raise e
                else:
                    log.warn('rebuilding js and css failed (not a problem)')
                    log.warn(str(e))
            command.run(self)
            update_package_data(self.distribution)
    return DecoratedCommand


def update_package_data(distribution):
    """update package_data to catch changes during setup"""
    build_py = distribution.get_command_obj('build_py')
    # distribution.package_data = find_package_data()
    # re-init build_py options which load package_data
    build_py.finalize_options()


# TODO: remove this function once we can depend on jupyter_packing, see:
#  https://github.com/voila-dashboards/voila/pull/322
# `run` function copied from jupyter_packaging under the following license:
# -------------------------------------------------------------------------
#
# BSD 3-Clause License
#
# Copyright (c) 2017, Project Jupyter
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
#
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
#
# * Neither the name of the copyright holder nor the names of its
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
def run(cmd, **kwargs):
    """Defaults to repo as cwd"""
    kwargs.setdefault('cwd', here)
    kwargs.setdefault('shell', os.name == 'nt')
    if not isinstance(cmd, (list, tuple)):
        cmd = shlex.split(cmd)
    cmd_path = shutil.which(cmd[0])
    if not cmd_path:
        sys.exit("Aborting. Could not find cmd (%s) in path. "
                 "If command is not expected to be in user's path, "
                 "use an absolute path." % cmd[0])
    cmd[0] = cmd_path
    return check_call(cmd, **kwargs)


class NPM(Command):
    description = 'install package.json dependencies using npm'

    user_options = []

    node_modules = os.path.join(node_root, 'node_modules')

    template_root = os.path.join(here, 'share', 'jupyter', 'voila', 'templates', 'base', 'static')
    targets = [
        os.path.join(template_root, 'voila.js')
    ]

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def has_npm(self):
        try:
            run(['npm', '--version'])
            return True
        except CalledProcessError:
            return False

    def should_run_npm_install(self):
        return self.has_npm()

    def run(self):
        if in_read_the_docs():
            log.warn(
                "Inside readthedocs -- skipping building JS dependencies.")
            return
        has_npm = self.has_npm()
        if not has_npm:
            log.error("`npm` unavailable.  If you're running this command using sudo, make sure `npm` is available to sudo")

        if self.should_run_npm_install():
            log.info('Installing build dependencies with npm.  This may take a while...')
            run(
                ['npm', 'install'],
                cwd=node_root,
                stdout=sys.stdout,
                stderr=sys.stderr
            )
            os.utime(self.node_modules, None)

        for t in self.targets:
            if not os.path.exists(t):
                msg = 'Missing file: %s' % t
                if not has_npm:
                    msg += '\nnpm is required to build a development version'
                raise ValueError(msg)

        # update package data in case this created new files
        self.distribution.data_files = get_data_files()

        # update package data in case this created new files
        update_package_data(self.distribution)


class BdistEggDisabled(bdist_egg):
    """Disabled version of bdist_egg

    Prevents setup.py install performing setuptools' default easy_install,
    which it should never ever do.
    """
    def run(self):
        sys.exit("Aborting implicit building of eggs. Use `pip install .` to install from source.")


cmdclass = {
    'jsdeps': NPM,
    'build_py': js_first(build_py),
    'egg_info': js_first(egg_info),
    'sdist': js_first(sdist, strict=True),
    'develop': develop,
    'bdist_egg': bdist_egg if 'bdist_egg' in sys.argv else BdistEggDisabled
}

version_ns = {}
with open(os.path.join(here, 'voila', '_version.py')) as f:
    exec(f.read(), {}, version_ns)


def get_data_files():
    """Get the data files for the package.
    """
    data_files = [
        ('etc/jupyter/jupyter_server_config.d', ['etc/jupyter/jupyter_server_config.d/voila.json']),
        ('etc/jupyter/jupyter_notebook_config.d', ['etc/jupyter/jupyter_notebook_config.d/voila.json']),
        ('etc/jupyter/nbconfig/notebook.d', ['etc/jupyter/nbconfig/notebook.d/voila.json']),
        ('share/jupyter/nbextensions/voila', ['voila/static/extension.js'])
    ]
    # Add all the templates
    for (dirpath, dirnames, filenames) in os.walk('share/jupyter/voila/templates/'):
        if filenames:
            data_files.append((dirpath, [os.path.join(dirpath, filename) for filename in filenames]))
    return data_files


setup_args = {
    'name': 'voila',
    'version': version_ns['__version__'],
    'description': 'Serving read-only live Jupyter notebooks',
    'packages': find_packages(),
    'zip_safe': False,
    'data_files': get_data_files(),
    'cmdclass': cmdclass,
    'package_data': {
        'voila': [
            'static/*'
        ]
    },
    'entry_points': {
        'console_scripts': [
            'voila = voila.app:main'
        ]
    },
    'install_requires': [
        'jupyter_server>=0.3.0,<0.4.0',
        'jupyter_client>=6.1.3,<7',
        'nbclient>=0.4.0,<0.5',
        'nbconvert==6.0.0a6'
    ],
    'extras_require': {
        'test': [
            'mock',
            'pytest',
            'pytest-tornasync',
            'matplotlib',
            'ipywidgets'
        ]
    },
    'url': 'https://github.com/voila-dashboards/voila',
    'author': 'Voilà Development team',
    'author_email': 'jupyter@googlegroups.com',
    'keywords': [
        'ipython',
        'jupyter',
        'widgets',
    ]
}

setup(**setup_args)

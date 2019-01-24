from setuptools import setup, find_packages, Command
from setuptools.command.sdist import sdist
from setuptools.command.build_py import build_py
from setuptools.command.egg_info import egg_info

from subprocess import check_call

import os
import sys

from distutils import log
log.set_verbosity(log.DEBUG)

here = os.path.dirname(os.path.abspath(__file__))
node_root = os.path.join(here, 'js')
is_repo = os.path.exists(os.path.join(here, '.git'))

npm_path = os.pathsep.join([
    os.path.join(node_root, 'node_modules', '.bin'),
                os.environ.get('PATH', os.defpath),
])

def in_read_the_docs():
    return os.environ.get('READTHEDOCS') == 'True'

def js_prerelease(command, strict=False):
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


class NPM(Command):
    description = 'install package.json dependencies using npm'

    user_options = []

    node_modules = os.path.join(node_root, 'node_modules')

    lib_root = os.path.join(here, 'voila', 'static')
    targets = [
        os.path.join(lib_root, 'libwidgets.js')
    ]

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def has_npm(self):
        try:
            check_call(['npm', '--version'])
            return True
        except:
            return False

    def should_run_npm_install(self):
        package_json = os.path.join(node_root, 'package.json')
        node_modules_exists = os.path.exists(self.node_modules)
        return self.has_npm()

    def run(self):
        if in_read_the_docs():
            log.warn(
                "Inside readthedocs -- skipping building JS dependencies.")
            return
        has_npm = self.has_npm()
        if not has_npm:
            log.error("`npm` unavailable.  If you're running this command using sudo, make sure `npm` is available to sudo")

        env = os.environ.copy()
        env['PATH'] = npm_path

        if self.should_run_npm_install():
            log.info('Installing build dependencies with npm.  This may take a while...')
            check_call(
                ['npm', 'install'],
                cwd=node_root,
                stdout=sys.stdout,
                stderr=sys.stderr
            )
            log.info('Building JS dependencies.')
            check_call(
                ['npm', 'run', 'build'],
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
        # update_package_data(self.distribution)

version_ns = {}
with open(os.path.join(here, 'voila', '_version.py')) as f:
    exec(f.read(), {}, version_ns)

data_files = [
    ('etc/jupyter/jupyter_server_config.d', ['etc/jupyter/jupyter_server_config.d/voila.json']),
    ('etc/jupyter/jupyter_notebook_config.d', ['etc/jupyter/jupyter_notebook_config.d/voila.json'])
]

# Add all the templates
for (dirpath, dirnames, filenames) in os.walk('share/jupyter/voila/template/'):
    if filenames:
        data_files.append((dirpath, [os.path.join(dirpath, filename) for filename in filenames]))

setup_args = {
    'name': 'voila',
    'version': version_ns['__version__'],
    'description': 'Serving read-only live Jupyter notebooks',
    'packages': find_packages(),
    'zip_safe': False,
    'data_files': data_files,
    'cmdclass': {
        'build_py': js_prerelease(build_py),
        'egg_info': js_prerelease(egg_info),
        'sdist': js_prerelease(sdist, strict=True),
        'jsdeps': NPM,
    },
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
        'jupyter_server',
        'nbconvert>=5.4,<6'
    ],
    'author': 'QuantStack',
    'author_email': 'info@quantstack.net',
    'keywords': [
        'ipython',
        'jupyter',
        'widgets',
    ]
}

setup(**setup_args)

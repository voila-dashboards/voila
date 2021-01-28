from jupyter_server.services.kernels.kernelmanager import AsyncMappingKernelManager
from nbclient.util import ensure_async
import asyncio
from traitlets import Unicode, Bool, Dict, List, Int, Enum
import tornado.ioloop


python_update_cwd_code = """
import os;
os.chdir({cwd!r});
del os;
"""

python_update_env_code = """
import os;
for key, value in {env!r}.items():
    os.environ[key] = value;
    del key
    del value
del os;
"""

python_init_import_code = """
import importlib
for name in {modules!r}:
    importlib.import_module(name)
    del name
del importlib
"""

class PoolMappingKernelManager(AsyncMappingKernelManager):
    initialization_code = Dict(
        help='Code that gets executed at startup'
    ).tag(config=True)
    pool_size_default = Int(1).tag(config=True)
    pool_size = Dict().tag(config=True)
    pool_names = List(Unicode(), ['python3'],
        help='List of kernel names for which to startup kernel pools at startup.',
    ).tag(config=True)
    python_imports = List(Unicode(), [], help='List of Python modules/packages to import').tag(config=True)

    wait_at_startup = Bool(True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # maps to lists the kernel ids
        self._kernel_pools = {kernel_name: [] for kernel_name in self.pool_names}
        ioloop = tornado.ioloop.IOLoop.current()
        self.log.info("Filling up kernel pool...")
        ioloop.run_sync(lambda: self.fill_pool(wait=self.wait_at_startup))

    async def fill_pool(self, wait=False):
        tasks = []
        for kernel_name in self.pool_names:
            pool = self._kernel_pools[kernel_name]
            current_size = len(pool)
            target_size = self.pool_size.get(kernel_name, self.pool_size_default)
            for _ in range(target_size - current_size):
                self.log.warning("Adding %s to pool", kernel_name)
                kernel_id_future = super(PoolMappingKernelManager, self).start_kernel(kernel_name=kernel_name)
                kernel_id_future = asyncio.create_task(self._initialize(kernel_name, kernel_id_future))
                tasks.append(kernel_id_future)
                self._kernel_pools[kernel_name].append(kernel_id_future)
        if wait:
            await asyncio.gather(*tasks)

    async def start_kernel(self, kernel_name=None, **kwargs):
        self.log.warning("Starting kernel: %s", kernel_name)
        if kernel_name in self.pool_names and self._kernel_pools[kernel_name]:
            self.log.warning("using pooled kernel")
            result = self._kernel_pools[kernel_name].pop(0)
            result = self._update_kernel(kernel_name, result, **kwargs)
            await self.fill_pool()
        else:
            result = super(PoolMappingKernelManager, self).start_kernel(kernel_name=kernel_name, **kwargs)
        return await result

    async def _update_kernel(self, kernel_name, kernel_id_future, **kwargs):
        # Make sure that the kernel is in a state that matches kwargs
        # Currently supported is a python3 kernel, and the path/cwd and env arguments
        if kernel_name == "python3" and kwargs:
            kernel_id = await kernel_id_future
            kernel = self.get_kernel(kernel_id)
            client = kernel.client()
            await ensure_async(client.start_channels())
            await ensure_async(client.wait_for_ready())
            if 'path' in kwargs:
                kwargs['cwd'] = self.cwd_for_path(kwargs.pop('path'))
            if 'cwd' in kwargs:
                cwd = kwargs.pop('cwd')
                code = python_update_cwd_code.format(cwd=cwd)
                self.log.debug("Updating preheated kernel CWD using: \n%s", code)
                client.execute(code)
                msg = await client.get_shell_msg()
                if msg['content']['status'] == 'error':
                    raise RuntimeError(f'Error executing cwd updating code: {msg}')
            if 'env' in kwargs:
                env = kwargs.pop('env')
                code = python_update_env_code.format(env=env)
                self.log.debug("Updating preheated kernel env vars using: \n%s", code)
                client.execute(code)
                msg = await client.get_shell_msg()
                if msg['content']['status'] == 'error':
                    raise RuntimeError(f'Error executing env updating code: {msg}')
            client.stop_channels()
        if kwargs:
            raise ValueError(f'Kernel pool does not support arguments {kwargs} for kernel {repr(kernel_name)}')

        return await kernel_id_future

    async def _initialize(self, kernel_name, kernel_id_future):
        kernel_id = await kernel_id_future

        language_to_extensions = {'python': 'py'}
        language = self.kernel_spec_manager.get_all_specs()[kernel_name]['spec']['language']
        if language not in language_to_extensions:
            self.log.error('No extension knows for language %r', language)
            return kernel_id
        extension = language_to_extensions[language]

        self.log.warning("Initializing kernel: %s", kernel_name)

        kernel = self.get_kernel(kernel_id)
        client = kernel.client()
        await ensure_async(client.start_channels())
        await ensure_async(client.wait_for_ready())
        from jupyter_core.paths import jupyter_config_path
        from pathlib import Path
        for base_path in map(Path, jupyter_config_path()):
            path = base_path / f'voila_kernel_pool_init_{kernel_name}.{extension}'
            self.log.debug('Checking %s for initializing kernel', path)
            if path.exists():
                with open(path) as f:
                    self.log.debug('Running %s for initializing kernel', path)
                    client.execute(f.read())
                msg = await client.get_shell_msg()
                if msg['content']['status'] == 'error':
                    raise RuntimeError(f'Error executing initialization code: {msg}')
        if language == 'python' and self.python_imports:
            code = python_init_import_code.format(modules=self.python_imports)
            client.execute(code)
            msg = await client.get_shell_msg()
            if msg['content']['status'] == 'error':
                raise RuntimeError(f'Error executing python import code: {msg}')
        client.stop_channels()
        return kernel_id

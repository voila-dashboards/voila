#############################################################################
# Copyright (c) 2021, Voilà Contributors                                    #
# Copyright (c) 2021, QuantStack                                            #
#                                                                           #
# Distributed under the terms of the BSD 3-Clause License.                  #
#                                                                           #
# The full license is in the file LICENSE, distributed with this software.  #
#############################################################################


import asyncio
import os
from typing import Awaitable, Coroutine, Type, TypeVar, Union
from typing import Dict as tDict
from pathlib import Path
from traitlets.traitlets import Bool, Dict, Float, List
from nbclient.util import ensure_async
import re
from .notebook_renderer import NotebookRenderer

T = TypeVar('T')


async def wait_before(delay: float, aw: Awaitable) -> Awaitable:
    await asyncio.sleep(delay)
    return await aw


def voila_kernel_manager_factory(base_class: Type[T], preheat_kernel: Bool) -> T:
    """
    Decorator used to make a normal kernel manager compatible with pre-heated
    kernel system.
    - If `preheat_kernel` is `False`, only two properties
    `notebook_data` and `notebook_html` are added to keep `NotebookRenderer`
    working, the kernel manager will work as it is.
    - If `preheat_kernel` is `True`, the input class is transformed to
     `VoilaKernelManager` with all the functionalities.

    Args:
        - base_class (Type[T]): The kernel manager class
        - preheat_kernel (Bool): Flag to decorate the input class

    Returns:
        T: Decorated class
    """
    if not preheat_kernel:

        class NormalKernelManager(base_class):
            def __init__(self, **kwargs) -> None:
                super().__init__(**kwargs)
                self.notebook_data: tDict = {}
                self.notebook_html: tDict = {}

            def start_kernel(
                self, kernel_name: Union[str, None] = None, **kwargs
            ) -> str:
                """Start a new kernel, because `NotebookRenderer` will call
                this method with `need_refill` paramenter so it need to be
                removed before passing to the original `start_kernel`.
                """
                kwargs.pop('need_refill', '')
                return super().start_kernel(kernel_name=kernel_name, **kwargs)

        return NormalKernelManager

    else:

        class VoilaKernelManager(base_class):
            """This class adds pooling heated kernels and pre-rendered notebook
            feature to a normal kernel manager. The 'pooling heated kernels'
            part is heavily inspired from `hotpot_km`(https://github.com/voila-dashboards/hotpot_km) library.
            """

            kernel_pools_size = Dict(
                {'default': {'kernel': 'python3', 'pool_size': 1}},
                config=True,
                help='Mapping from notebook name to the number of started kernels to keep on standby.',
            )

            preheat_blacklist = List([],
                                     config=True,
                                     help='List of notebooks which do not use pre-heated kernel.')

            fill_delay = Float(
                1,
                config=True,
                help='Wait time before re-filling the pool after a kernel is used',
            )

            kernel_env_variables = Dict(
                {}, config=True, help='Environnement variables used to start kernel.'
            )

            def __init__(self, **kwargs):

                super().__init__(**kwargs)
                self._wait_at_startup = True
                self.notebook_data: tDict = {}
                self.notebook_html: tDict = {}
                self._pools: tDict[str, Union[str, Coroutine[str]]] = {}
                self.root_dir = self.parent.root_dir
                print(self.parent.notebook_path, self.root_dir)
                if self.parent.notebook_path is not None:
                    self.notebook_path = os.path.relpath(
                        self.parent.notebook_path, self.root_dir
                    )
                    self.fill_if_needed(delay=0, notebook_name=self.notebook_path)
                else:
                    self.notebook_path = None
                    all_notebooks = [
                        x.relative_to(self.root_dir)
                        for x in list(Path(self.root_dir).rglob('*.ipynb'))
                        if self._notebook_filter(x)
                    ]
                    for nb in all_notebooks:
                        self.fill_if_needed(delay=0, notebook_name=str(nb))
                # for key in self.kernel_pools_size:

            async def start_kernel(
                self, kernel_name: Union[str, None] = None, **kwargs
            ) -> str:
                """Depend on `need_refill` flag, this method will pop a kernel from pool or start a new
                kernel.
                """
                need_refill = kwargs.pop('need_refill', None)
                if kernel_name is None:
                    kernel_name = self.default_kernel_name

                if (
                    need_refill is not None
                    and len(self._pools.get(need_refill, ())) > 0
                ):
                    kernel_id = await self._pop_pooled_kernel(need_refill, **kwargs)
                    self.log.info('Using pre-heated kernel: %s for %s', kernel_id, need_refill)
                    self.fill_if_needed(delay=None, notebook_name=need_refill, **kwargs)
                else:
                    kernel_id = await super().start_kernel(
                        kernel_name=kernel_name, **kwargs
                    )
                return kernel_id

            async def _pop_pooled_kernel(
                self, kernel_name: Union[str, None], **kwargs
            ) -> str:
                """Return a pre-heated kernel's id from pool

                Args:
                    -kernel_name (Union[str, None]): Name of kernel
                    pool

                Returns:
                    str: Kernel id.
                """
                fut = self._pools[kernel_name].pop(0)
                return await fut

            def fill_if_needed(
                self,
                delay: Union[float, None] = None,
                notebook_name: Union[str, None] = None,
                **kwargs,
            ) -> None:
                """Start kernels until the pool is full

                Args:
                    - delay (Union[float, None], optional): Delay time before
                    starting refill kernel. Defaults to None.
                    - notebook_name (Union[str, None], optional): Name of notebook to
                    create kernel pool.
                    Defaults to None.
                """
                delay = delay if delay is not None else self.fill_delay
                try:
                    loop = asyncio.get_event_loop()
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                if notebook_name in self.kernel_pools_size:
                    kernel_name = self.kernel_pools_size[notebook_name].get(
                        'kernel', 'python3'
                    )
                    kernel_size = self.kernel_pools_size[notebook_name].get(
                        'pool_size', 1
                    )
                else:
                    default_config = self.kernel_pools_size.get('default', {})
                    kernel_name = default_config.get('kernel', 'python3')
                    kernel_size = default_config.get('pool_size', 1)
                pool = self._pools.get(notebook_name, [])
                self._pools[notebook_name] = pool
                if 'path' not in kwargs:
                    kwargs['path'] = (
                        os.path.dirname(notebook_name)
                        if notebook_name is not None
                        else self.root_dir
                    )
                kernel_env = kwargs.get('env', {})
                for key in self.kernel_env_variables:
                    if key not in kernel_env:
                        kernel_env[key] = self.kernel_env_variables[key]
                kwargs['env'] = kernel_env

                heated = len(pool)

                def task_counter(tk):
                    nonlocal heated
                    heated += 1
                    if (heated == kernel_size):
                        self.log.info(
                            'Kernel pool of %s is filled with %s kernel(s)', notebook_name, kernel_size
                        )

                for _ in range(kernel_size - len(pool)):
                    fut = super().start_kernel(kernel_name=kernel_name, **kwargs)
                    # Start the work on the loop immediately, so it is ready when needed:
                    task = loop.create_task(
                        wait_before(delay, self._initialize(fut, notebook_name))
                    )
                    pool.append(task)
                    task.add_done_callback(task_counter)

            async def restart_kernel(self, kernel_id: str, **kwargs) -> None:
                await ensure_async(super().restart_kernel(kernel_id, **kwargs))
                notebook_name = self.notebook_html.get(kernel_id, [None, ''])[0]
                id_future = asyncio.Future()
                id_future.set_result(kernel_id)
                if notebook_name is not None:
                    await self._initialize(id_future, notebook_name)

            async def shutdown_kernel(self, kernel_id: str, *args, **kwargs):
                for pool in self._pools.values():
                    for i, f in enumerate(pool):
                        if f.done() and f.result() == kernel_id:
                            pool.pop(i)
                            break
                    else:
                        continue
                    break
                self.notebook_html.pop(kernel_id, None)
                return await ensure_async(
                    super().shutdown_kernel(kernel_id, *args, **kwargs)
                )

            async def shutdown_all(self, *args, **kwargs):
                await ensure_async(super().shutdown_all(*args, **kwargs))
                # Parent doesn't correctly add all created kernels until they have completed startup:
                pools = self._pools
                self._pools = {}
                for pool in pools.values():
                    # The iteration gets confused if we don't copy pool
                    for fut in tuple(pool):
                        try:
                            kid = await fut
                        except Exception:
                            pass
                        else:
                            if kid in self:
                                await ensure_async(
                                    self.shutdown_kernel(kid, *args, **kwargs)
                                )

            async def _initialize(
                    self, kernel_id_future: str, notebook_path: str) -> str:
                """Run any configured initialization code in the kernel"""
                kernel_id = await kernel_id_future
                gen = self._notebook_renderer_factory(notebook_path)
                await gen.initialize()

                kernel_name = gen.notebook.metadata.kernelspec.name
                if notebook_path in self.kernel_pools_size:
                    kernel_in_pool = self.kernel_pools_size[notebook_path]['kernel']
                else:
                    kernel_in_pool = self.kernel_pools_size.get('default', {}).get(
                        'kernel', None
                    )
                if kernel_in_pool != kernel_name:
                    self.log.warning(
                        f'Kernel for {notebook_path} is not heated! Please check `kernel_pools_size` configuration'
                    )
                    return kernel_id
                kernel_future = self.get_kernel(kernel_id)
                self.notebook_html[kernel_id] = [
                    notebook_path,
                    await gen.generate_html_str(kernel_id, kernel_future),
                ]
                self.notebook_data[gen.notebook_path] = {
                    'notebook': gen.notebook,
                    'template': gen.template_name,
                    'theme': gen.theme,
                }
                return kernel_id

            async def cull_kernel_if_idle(self, kernel_id: str):
                """Ensure we don't cull pooled kernels:
                (this logic assumes the init time is shorter than the cull time)
                """

                for pool in self._pools.values():
                    for i, f in enumerate(pool):
                        try:
                            if f.done() and f.result() == kernel_id:
                                return
                        except Exception:
                            pool.pop(i)
                return await ensure_async(super().cull_kernel_if_idle(kernel_id))

            def _notebook_renderer_factory(
                self, notebook_path: Union[str, None] = None
            ) -> NotebookRenderer:
                """Helper function to create `NotebookRenderer` instance.

                Args:
                    - notebook_path (Union[str, None], optional): Path to the
                    notebook. Defaults to None.
                """
                return NotebookRenderer(
                    voila_configuration=self.parent.voila_configuration,
                    traitlet_config=self.parent.config,
                    notebook_path=notebook_path,
                    template_paths=self.parent.template_paths,
                    config_manager=self.parent.config_manager,
                    contents_manager=self.parent.contents_manager,
                    base_url=self.parent.base_url,
                    kernel_spec_manager=self.parent.kernel_spec_manager,
                )

            def _notebook_filter(self, nb_path: Path) -> bool:
                nb_name = str(nb_path)
                if '.ipynb_checkpoints' in nb_name:
                    return False
                for nb_pattern in self.preheat_blacklist:
                    pattern = re.compile(nb_pattern)
                    if (nb_pattern in nb_name) or bool(pattern.match(nb_name)):
                        return False
                return True

    return VoilaKernelManager

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
from typing import Any, Awaitable, Coroutine, Type, TypeVar, Union
from typing import Dict as tDict

from traitlets.traitlets import Bool, Dict, Float
from nbclient.util import ensure_async

from .notebook_renderer import NotebookRenderer

T = TypeVar('T')


async def wait_before(delay: float, aw : Awaitable) -> Awaitable:
    await asyncio.sleep(delay)
    return await aw


def voila_kernel_manager_factory(base_class: Type[T], preheat_kernel: Bool) -> T:
    if not preheat_kernel:

        class NormalKernelManager(base_class):
            def __init__(self, **kwargs) -> None:
                super().__init__(**kwargs)
                self.notebook_data: tDict = {}
                self.notebook_html: tDict = {}

            def start_kernel(
                self, kernel_name: Union[str, None] = None, **kwargs
            ) -> str:
                kwargs.pop('need_refill', False)
                return super().start_kernel(kernel_name=kernel_name, **kwargs)

        return NormalKernelManager

    else:

        class VoilaKernelManager(base_class):
            """ This class adds pooling heated kernels and pre-rendered notebook
            feature to a normal kernel manager. The 'pooling heated kernels'
            part is heavily inspired from `hotpot_km`(https://github.com/voila-dashboards/hotpot_km) library.
            """

            kernel_pools_size = Dict(
                {'python3': 3},
                config=True,
                help='Mapping from kernel name to the number of started kernels to keep on standby.'
            )

            fill_delay = Float(
                1,
                config=True,
                help='Wait time before re-filling the pool after a kernel is used',
            )

            kernel_env_variables = Dict(
                {},
                config=True,
                help='Environnement variables used to start kernel.'
            )

            def __init__(self, **kwargs):

                super().__init__(**kwargs)
                self._wait_at_startup = True
                self.notebook_data: tDict = {}
                self.notebook_html: tDict = {}
                self._pools: tDict[str, Union[str, Coroutine[str]]] = {}
                for key in self.kernel_pools_size:
                    self.fill_if_needed(delay=0, kernel_name=key)

            async def start_kernel(
                self, kernel_name: Union[str, None] = None, **kwargs
            ) -> str:
                need_refill = kwargs.pop('need_refill', False)
                if kernel_name is None:
                    kernel_name = self.default_kernel_name

                if need_refill and len(self._pools.get(kernel_name, ())) > 0:
                    kernel_id = await self._pop_pooled_kernel(kernel_name, **kwargs)
                    self.log.info('Using pre-heated kernel: %s', kernel_id)
                    self.fill_if_needed(delay=None, kernel_name=kernel_name, **kwargs)
                else:
                    kernel_id = await super().start_kernel(
                        kernel_name=kernel_name, **kwargs
                    )
                return kernel_id

            async def _pop_pooled_kernel(
                self, kernel_name: Union[str, None], **kwargs
            ) -> Coroutine[Any, Any, str]:
                fut = self._pools[kernel_name].pop(0)
                return await fut

            def fill_if_needed(
                self,
                delay: Union[float, None] = None,
                kernel_name: Union[str, None] = None,
                **kwargs,
            ) -> None:
                """Start kernels until pool is full"""
                delay = delay if delay is not None else self.fill_delay
                try:
                    loop = asyncio.get_event_loop()
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                target = self.kernel_pools_size.get(kernel_name, 0)
                pool = self._pools.get(kernel_name, [])
                self._pools[kernel_name] = pool
                notebook_path = self.parent.notebook_path
                if 'path' not in kwargs:
                    kwargs['path'] = (
                        os.path.dirname(notebook_path)
                        if notebook_path is not None
                        else self.parent.root_dir
                    )
                kernel_env = kwargs.get('env', {})
                for key in self.kernel_env_variables:
                    if key not in kernel_env:
                        kernel_env[key] = self.kernel_env_variables[key]
                kwargs['env'] = kernel_env

                for _ in range(target - len(pool)):
                    fut = super().start_kernel(kernel_name=kernel_name, **kwargs)
                    # Start the work on the loop immediately, so it is ready when needed:
                    task = loop.create_task(wait_before(delay, self._initialize(fut)))
                    pool.append(task)

            async def restart_kernel(self, kernel_id: str, **kwargs) -> None:
                await ensure_async(super().restart_kernel(kernel_id, **kwargs)) 
                id_future = asyncio.Future()
                id_future.set_result(kernel_id)
                await self._initialize(id_future)

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
                return await ensure_async(super().shutdown_kernel(kernel_id, *args, **kwargs)) 

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
                        if kid in self:
                            await ensure_async(self.shutdown_kernel(kid, *args, **kwargs)) 

            async def _initialize(self, kernel_id_future: str) -> str:
                """Run any configured initialization code in the kernel"""
                kernel_id = await kernel_id_future
                if self.parent.notebook_path is None:
                    return kernel_id
                notebook_path = os.path.relpath(
                    self.parent.notebook_path, self.parent.root_dir
                )
                gen = self._notebook_renderer_factory(notebook_path)
                await gen.initialize()
                kernel_future = self.get_kernel(kernel_id)
                self.notebook_html[kernel_id] = await gen.generate_html_str(
                    kernel_id, kernel_future
                )
                self.notebook_data[gen.notebook_path] = {
                    'notebook': gen.notebook,
                    'template': gen.template_name,
                    'theme': gen.theme,
                }

                self.log.info(f'Pre-headted kernel: %s', kernel_id)
                return kernel_id

            async def cull_kernel_if_idle(self, kernel_id: str):
                # Ensure we don't cull pooled kernels:
                # (this logic assumes the init time is shorter than the cull time)
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

    return VoilaKernelManager

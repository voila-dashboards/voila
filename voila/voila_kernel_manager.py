
from jupyter_server.services import config
from .notebook_renderer import NotebookRenderer
from typing import  Any, Callable, Union, Coroutine, TypeVar, Type
from typing import Dict as tDict
from traitlets.traitlets import Bool, Unicode, Dict, Float, Integer
import asyncio


T = TypeVar('T')

async def wait_before(delay, aw):
    await asyncio.sleep(delay)
    return await aw


def voila_kernel_manager_factory(base_class : Type[T], preheat_kernel : Bool, notebook_renderer_factory : Callable) -> T:

    if not preheat_kernel:
        class NormalKernelManager(base_class):
            def __init__(self, **kwargs) -> None:
                super().__init__(**kwargs)
                self.notebook_model: tDict = {}
                self.notebook_html: tDict = {}
 
            def start_kernel(self, kernel_name: Union[str, None]=None,
            **kwargs) -> str:
                kwargs.pop('need_refill', False)
                return super().start_kernel(kernel_name=kernel_name, **kwargs)
        return NormalKernelManager

    else:
        class VoilaKernelManager(base_class):

            kernel_pools_size = Dict(
                { 'python3': 3},
                config=True,
                help="""Configuration for VoilaKernelManager.
                """
            )

            fill_delay = Float(
                1,
                config=True,
                help="Wait time before re-filling the pool after a kernel is used",
            )

            def __init__(self, **kwargs):
                
                self.notebook_renderer_factory = notebook_renderer_factory
                super().__init__(**kwargs)
                self._wait_at_startup = True
                self.notebook_model: tDict = {}
                self.notebook_html: tDict = {}
                self._pools: tDict[str, Union[str, Coroutine[str]]] = {}
                for key in self.kernel_pools_size:
                    self.fill_if_needed(delay=0, kernel_name=key)

            async def start_kernel(self, kernel_name: Union[str, None]=None,
            **kwargs) -> str:
                need_refill = kwargs.pop('need_refill', False)
                if kernel_name is None:
                    kernel_name = self.default_kernel_name
                self.log.info("Starting kernel: %s", kernel_name)

                if need_refill and len(self._pools.get(kernel_name, ())) > 0:
                    kernel_id = await self._pop_pooled_kernel(kernel_name, **kwargs)
                    self.fill_if_needed(delay = None, kernel_name = kernel_name, **kwargs)
                else:
                    kernel_id = await super().start_kernel(kernel_name=kernel_name, **kwargs)      
                return kernel_id

            async def _pop_pooled_kernel(self, kernel_name: Union[str, None], **kwargs) -> Coroutine[Any, Any, str]:
                fut = self._pools[kernel_name].pop(0)
                return await fut

            def fill_if_needed(self, delay: Union[float, None]=None, kernel_name: Union[str, None]=None, **kwargs)-> None:
                """Start kernels until pool is full"""
                delay = delay if delay is not None else self.fill_delay
                try:
                    loop = asyncio.get_event_loop()
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                target =  self.kernel_pools_size.get(kernel_name, 0)
                pool = self._pools.get(kernel_name, [])
                self._pools[kernel_name] = pool
                for _ in range(target - len(pool)):
                    fut = super().start_kernel(kernel_name=kernel_name, **kwargs)
                    # Start the work on the loop immediately, so it is ready when needed:
                    task = loop.create_task(wait_before(delay, self._initialize(fut)))
                    pool.append(task)

            async def restart_kernel(self, kernel_id: str, **kwargs)-> None:
                await super().restart_kernel(kernel_id, **kwargs)
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
                return await super().shutdown_kernel(kernel_id, *args, **kwargs)

            async def shutdown_all(self, *args, **kwargs):
                await super().shutdown_all(*args, **kwargs)
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
                            await self.shutdown_kernel(kid, *args, **kwargs)
                try:
                    asyncio.gather(*self._discarded)
                except Exception:
                    pass
                self._discarded = []

            async def _initialize(self, kernel_id_future: str)->str:
                """Run any configured initialization code in the kernel"""
                kernel_id = await kernel_id_future
                self.log.info("Initializing kernel: %s", kernel_id)
                gen = self.notebook_renderer_factory()
                await gen.initialize()
                kernel_future = self.get_kernel(kernel_id)
                self.notebook_html[kernel_id] = await gen.generate_html_str(
                    kernel_id, kernel_future
                )

                self.notebook_model[gen.notebook_path] = gen.notebook

                self.log.info(f"Initialized kernel: length {len(self.notebook_html)}")
                self.initialized_kernel_id = kernel_id
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
                return await super().cull_kernel_if_idle(kernel_id)

    return VoilaKernelManager


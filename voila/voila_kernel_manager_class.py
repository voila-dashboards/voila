from hotpot_km.mapping import PooledMappingKernelManager, PooledKernelManager
from jupyter_server.services import config
from .notebook_renderer import NotebookRenderer
from typing import  Any, Union, Coroutine
from traitlets.traitlets import Unicode, Dict, Float, Integer
from .configuration import VoilaConfiguration
import asyncio

async def wait_before(delay, aw):
    await asyncio.sleep(delay)
    return await aw


async def await_then_kill(km, aw_id):
    return await km.shutdown_kernel(await aw_id)
def ensure_event_loop():
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop


def voila_kernel_manager_factory():
    voila_configuration = VoilaConfiguration()
    print(voila_configuration.multi_kernel_manager_class)
    class VoilaKernelManager(voila_configuration.multi_kernel_manager_class):

        kernel_pools = Dict(
            Integer(0),
            config=True,
            help="Mapping from kernel name to the number of started kernels to keep on standby",
        )

        fill_delay = Float(
            1,
            config=True,
            help="Wait time before re-filling the pool after a kernel is used",
        )

        def __init__(self, **kwargs) -> None:
            self.notebook_renderer_factory = kwargs.pop("notebook_renderer_factory", None)
            super().__init__(**kwargs)
            self.kernel_pools = {"python3": 3}
            self._wait_at_startup = True
            self.notebook_model: Dict = {}
            self.notebook_html: Dict = {}
            self._pools: Dict[str, Union[str, Coroutine[str]]] = {}

        async def start_kernel(self, kernel_name: Union[str, None]=None, need_refill: bool=True,  **kwargs) -> str:
            print('refill', need_refill)
            if kernel_name is None:
                kernel_name = self.default_kernel_name
            self.log.debug("Starting kernel: %s", kernel_name)
            kernel_id = kwargs.get("kernel_id")
            if need_refill and len(self._pools.get(kernel_name, ())) > 0:
                kernel_id = await self._pop_pooled_kernel(kernel_name, kwargs)
                self.fill_if_needed(delay = None, kernel_name=None, **kwargs)
            else:
                kernel_id = await super().start_kernel(kernel_name=kernel_name, **kwargs)

            
            return kernel_id

        async def _pop_pooled_kernel(self, kernel_name: Union[str, None], **kwargs) -> Coroutine[Any, Any, str]:
            fut = self._pools[kernel_name].pop(0)
            return await fut

        def fill_if_needed(self, delay: Union[float, None]=None, kernel_name: Union[str, None]=None, **kwargs):
            """Start kernels until pool is full"""
            delay = delay if delay is not None else self.fill_delay
            loop = ensure_event_loop()
            target =  self.kernel_pools.get(kernel_name, 0)
            pool = self._pools.get(kernel_name, [])
            self._pools[kernel_name] = pool
            for i in range(target - len(pool)):
                print('refill kernel', i)
                fut = super().start_kernel(kernel_name=kernel_name, **kwargs)
                # Start the work on the loop immediately, so it is ready when needed:
                task = loop.create_task(wait_before(delay, self._initialize(kernel_name, fut)))
                pool.append(task)

    return VoilaKernelManager


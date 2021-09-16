from hotpot_km.mapping import PooledMappingKernelManager, PooledKernelManager
from .notebook_renderer import NotebookRenderer
from typing import Dict, Union
from traitlets.traitlets import Unicode


class VoilaKernelManager(PooledMappingKernelManager):
    def __init__(self, *args, **kwargs):
        self.notebook_renderer_factory = kwargs.pop("notebook_renderer_factory", None)

        super().__init__(*args, **kwargs)
        self.kernel_pools = {"python3": 3}
        self._wait_at_startup = True
        self.notebook_model: Dict = {}
        self.notebook_html: Dict = {}

    async def start_kernel(self, kernel_name=None, need_refill=True, **kwargs):
        if need_refill:
            return await super().start_kernel(kernel_name=None, **kwargs)
        else:
            return await super(PooledKernelManager, self).start_kernel(
                kernel_name=kernel_name, **kwargs
            )

    async def _initialize(self, kernel_name, kernel_id_future):
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

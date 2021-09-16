from hotpot_km.mapping import PooledMappingKernelManager, PooledKernelManager
from .notebook_renderer import NotebookRenderer
from typing import Dict, Union
from traitlets.traitlets import Unicode

class VoilaKernelManager(PooledMappingKernelManager):
    def __init__(self, *args, **kwargs):
        self.traitlet_config = kwargs.pop("traitlet_config", None)
        self.voila_configuration = kwargs.pop("voila_configuration", None)
        self.notebook_path = kwargs.pop("notebook_path", None)
        self.template_paths = kwargs.pop("template_paths", None)
        self.config_manager = kwargs.pop("config_manager", None)
        self.contents_manager = kwargs.pop("contents_manager", None)
        self.kernel_manager = kwargs.pop("kernel_manager", None)
        self._kernel_spec_manager = kwargs.get("kernel_spec_manager")

        super().__init__(*args, **kwargs)
        self.kernel_pools = {"python3": 3}
        self._wait_at_startup = True
        self.notebook_model: Dict = {}
        self.notebook_html: Dict = {}

    async def start_kernel(self, kernel_name=None, need_refill = True, **kwargs):
        if need_refill:
            return await super().start_kernel(kernel_name=None, **kwargs)
        else:
            return await super(PooledKernelManager, self).start_kernel(kernel_name=kernel_name, **kwargs)
         

    async def _initialize(self, kernel_name, kernel_id_future):
        """Run any configured initialization code in the kernel"""
        kernel_id = await kernel_id_future
        self.log.info("Initializing kernel: %s", kernel_id)
        gen = NotebookRenderer(
            voila_configuration=self.voila_configuration,
            traitlet_config=self.traitlet_config,
            notebook_path=self.notebook_path,
            template_paths=self.template_paths,
            config_manager=self.config_manager,
            contents_manager=self.contents_manager,
            kernel_manager=self,
            kernel_spec_manager=self._kernel_spec_manager,
        )
        await gen.initialize()
        kernel_future = self.get_kernel(kernel_id)
        await gen.generate_html_str(kernel_id, kernel_future)
        self.notebook_html[kernel_id] =  gen.html
        self.notebook_model[self.notebook_path] =  gen.notebook

        self.log.info(f"Initialized kernel: length {len(self.notebook_html)}" )
        self.initialized_kernel_id = kernel_id
        return kernel_id

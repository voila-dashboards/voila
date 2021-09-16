from os import wait
from hotpot_km.mapping import PooledMappingKernelManager
from .execute import VoilaExecutor
from .utils import GenerateNotebook
from hotpot_km.client_helper import DeadKernelError
from hotpot_km.limited import MaximumKernelsException
from typing import Union

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
        self.initialization_code = {"python3": 'print("1+2")'}
        self.notebook_html = {}
        print('path', self.notebook_path)

    async def start_kernel(self, kernel_name=None, **kwargs):
        if kernel_name is None:
            kernel_name = self.default_kernel_name
        self.log.debug("Starting kernel: %s", kernel_name)
        kernel_id = kwargs.get("kernel_id")
        while kernel_id is None and self._should_use_pool(kernel_name, kwargs):
            try:
                kernel_id = await self._pop_pooled_kernel(kernel_name, kwargs)

            except (MaximumKernelsException, DeadKernelError):
                pass
        if kernel_id is None or kwargs.get("kernel_id") is not None:
            kernel_id = await super().start_kernel(kernel_name=kernel_name, **kwargs)

        self.fill_if_needed()
        return kernel_id

    def get_notebook_html(self, kernel_id: Union[str, None] = None ) -> Union[str, None] :
        if kernel_id is not None:
            return self.notebook_html.get(kernel_id, None)
        else:
            key_list = list(self.notebook_html)
            if len(key_list)> 0:
                return self.notebook_html[key_list[0]]
            else:
                return None

    async def _initialize(self, kernel_name, kernel_id_future):
        """Run any configured initialization code in the kernel"""
        kernel_id = await kernel_id_future
        kernel = self.get_kernel(kernel_id)

        self.log.info("Initializing kernel: %s", kernel_id)
        gen = GenerateNotebook(
            voila_configuration=self.voila_configuration,
            traitlet_config=self.traitlet_config,
            notebook_path=self.notebook_path,
            template_paths=self.template_paths,
            config_manager=self.config_manager,
            contents_manager=self.contents_manager,
            kernel_manager=self,
            kernel_spec_manager=self._kernel_spec_manager,
            kernel_id=kernel_id
        )
        await gen.generate()
        self.notebook_html[kernel_id] = gen.html
        self.log.info("Initialized kernel: %s", kernel_id)
        return kernel_id

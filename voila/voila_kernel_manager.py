from hotpot_km.mapping import PooledMappingKernelManager
from .notebook_renderer import NotebookRenderer
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
        self.notebook_html = {}


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
        await gen.generate(kernel_id)
        self.notebook_html[kernel_id] = gen.html
        self.log.info("Initialized kernel: %s", kernel_id)
        return kernel_id

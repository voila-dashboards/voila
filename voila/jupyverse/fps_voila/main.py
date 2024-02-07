import pkg_resources

from asphalt.core import Component, ContainerComponent, Context
from jupyverse_api.app import App
from jupyverse_api.auth import Auth

from .routes import Voila


class VoilaComponent(Component):
    def __init__(
        self,
        *,
        settings,
        voila_configuration,
        static_paths,
        base_url,
    ):
        super().__init__()
        self.settings = settings
        self.voila_configuration = voila_configuration
        self.static_paths = static_paths
        self.base_url = base_url

    async def start(
        self,
        ctx: Context,
    ) -> None:
        app = await ctx.request_resource(App)
        auth = await ctx.request_resource(Auth)

        voila = Voila(
            app,
            auth,
            self.settings,
            self.voila_configuration,
            self.static_paths,
            self.base_url,
        )
        ctx.add_resource(voila)


class RootComponent(ContainerComponent):
    def __init__(
        self,
        settings,
        voila_configuration,
        static_paths,
        base_url,
        ip,
        port,
    ):
        super().__init__()
        self.settings = settings
        self.voila_configuration = voila_configuration
        self.static_paths = static_paths
        self.base_url = base_url
        self.ip = ip
        self.port = port

    async def start(self, ctx: Context) -> None:
        asphalt_components = {
            ep.name: ep
            for ep in pkg_resources.iter_entry_points(group="asphalt.components")
        }

        self.add_component(
            "fastapi",
            asphalt_components["fastapi"].load(),
            host=self.ip,
            port=self.port,
        )
        self.add_component(
            "voila",
            asphalt_components["voila"].load(),
            settings=self.settings,
            voila_configuration=self.voila_configuration,
            static_paths=self.static_paths,
            base_url=self.base_url,
        )
        self.add_component(
            "contents",
            asphalt_components["contents"].load(),
            prefix="/voila",
        )
        self.add_component(
            "auth",
            asphalt_components["noauth"].load(),
        )
        self.add_component(
            "app",
            asphalt_components["app"].load(),
        )
        await super().start(ctx)

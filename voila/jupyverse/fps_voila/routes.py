import logging
from typing import List

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from starlette.staticfiles import PathLike, StaticFiles
from jupyverse_api import Router
from jupyverse_api.app import App
from jupyverse_api.auth import Auth
from voila.utils import get_page_config


logger = logging.getLogger(__name__)


class Voila(Router):
    def __init__(
        self,
        app: App,
        auth: Auth,
        settings,
        voila_configuration,
        static_paths,
        base_url,
    ):
        super().__init__(app=app)

        router = APIRouter()

        @router.get("/", response_class=HTMLResponse)
        async def get_root(request: Request):
            page_config = get_page_config(
                base_url=base_url,
                settings=settings,
                log=logger,
                voila_configuration=voila_configuration,
            )
            template = settings["voila_jinja2_env"].get_template("tree-lab.html")
            return template.render(
                page_config=page_config,
            )

        self.include_router(router)

        self.mount(
            "/voila/static",
            MultiStaticFiles(directories=static_paths, check_dir=False),
        )


class MultiStaticFiles(StaticFiles):
    def __init__(self, directories: List[PathLike] = [], **kwargs) -> None:
        super().__init__(**kwargs)
        self.all_directories = self.all_directories + directories

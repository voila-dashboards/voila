import sys
import os
import uuid
from pathlib import Path
from typing import Optional

from voila.handler import _VoilaHandler, _get

from mimetypes import guess_type
from fastapi import APIRouter, Depends
from fastapi.responses import RedirectResponse, StreamingResponse, Response
from fastapi.staticfiles import StaticFiles
from fps.hooks import register_router  # type: ignore

from .config import get_voila_config


class FPSVoilaHandler(_VoilaHandler):
    is_fps = True
    fps_arguments = {}
    html = []

    def redirect(self, url):
        return RedirectResponse(url)

    def get_argument(self, name, default):
        if self.fps_arguments[name] is None:
            return default
        return self.fps_arguments[name]


def init_voila_handler(
    notebook_path,
    template_paths,
    config,
    voila_configuration,
    contents_manager,
    base_url,
    kernel_manager,
    kernel_spec_manager,
    allow_remote_access,
    autoreload,
    voila_jinja2_env,
    jinja2_env,
    static_path,
    server_root_dir,
    config_manager,
    static_paths,
):
    global fps_voila_handler
    fps_voila_handler = FPSVoilaHandler()
    fps_voila_handler.initialize(
        notebook_path=notebook_path,
        template_paths=template_paths,
        traitlet_config=config,
        voila_configuration=voila_configuration,
    )
    fps_voila_handler.contents_manager = contents_manager
    fps_voila_handler.base_url = base_url
    fps_voila_handler.kernel_manager = kernel_manager
    fps_voila_handler.kernel_spec_manager = kernel_spec_manager
    fps_voila_handler.allow_remote_access = allow_remote_access
    fps_voila_handler.autoreload = autoreload
    fps_voila_handler.voila_jinja2_env = voila_jinja2_env
    fps_voila_handler.jinja2_env = jinja2_env
    fps_voila_handler.static_path = static_path
    fps_voila_handler.server_root_dir = server_root_dir
    fps_voila_handler.config_manager = config_manager
    fps_voila_handler.static_paths = static_paths


router = APIRouter()

@router.get("/")
async def get_root(voila_template: Optional[str] = None, voila_theme: Optional[str] = None, voila_config=Depends(get_voila_config)):
    fps_voila_handler.fps_arguments["voila-template"] = voila_template
    fps_voila_handler.fps_arguments["voila-theme"] = voila_theme
    path = "" #voila_config.notebook_path or "/"
    return StreamingResponse(_get(fps_voila_handler, path))

@router.get("/voila/static/{path}")
def get_file1(path):
    return get_file(path)

@router.get("/voila/templates/lab/static/{path:path}")
def get_file2(path):
    return get_file(path)

def get_file(path):
    for i, static_path in enumerate(fps_voila_handler.static_paths):
        file_path = Path(static_path) / path
        if os.path.exists(file_path):
            with open(file_path) as f:
                content = f.read()
            content_type, _ = guess_type(file_path)
            return Response(content, media_type=content_type)

r = register_router(router)

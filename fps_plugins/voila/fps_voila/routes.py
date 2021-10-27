import re
import os
from pathlib import Path
from typing import Optional

from voila.handler import _VoilaHandler, _get
from voila.treehandler import _VoilaTreeHandler, _get as _get_tree

from mimetypes import guess_type
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse, StreamingResponse, HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
from fps.hooks import register_router  # type: ignore

from .config import get_voila_config


class Config:
    pass

CONFIG = Config()

class FPSVoilaTreeHandler(_VoilaTreeHandler):
    is_fps = True

    def redirect(self, url):
        return RedirectResponse(url)

    def write(self, html):
        return HTMLResponse(html)

    def render_template(self, name, **kwargs):
        kwargs["base_url"] = self.base_url
        template = self.jinja2_env.get_template(name)
        return template.render(**kwargs)


class FPSVoilaHandler(_VoilaHandler):
    is_fps = True
    fps_arguments = {}
    html = []

    def redirect(self, url):
        return RedirectResponse(url)

    def get_argument(self, name, default):
        if self.fps_arguments.get(name) is None:
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
    settings,
    log,
    whitelist,
    blacklist,
    root_dir,
):
    global fps_voila_handler, fps_voila_tree_handler

    CONFIG.whitelist = whitelist
    CONFIG.blacklist = blacklist
    CONFIG.root_dir = root_dir

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

    fps_voila_tree_handler = FPSVoilaTreeHandler()
    fps_voila_tree_handler.initialize(
        voila_configuration=voila_configuration,
    )
    fps_voila_tree_handler.contents_manager = contents_manager
    fps_voila_tree_handler.base_url = base_url
    fps_voila_tree_handler.voila_jinja2_env = voila_jinja2_env
    fps_voila_tree_handler.jinja2_env = jinja2_env
    fps_voila_tree_handler.settings = settings
    fps_voila_tree_handler.log = log
    settings["contents_manager"] = contents_manager


router = APIRouter()

@router.get("/notebooks/{path:path}")
async def get_root(path, voila_template: Optional[str] = None, voila_theme: Optional[str] = None, voila_config=Depends(get_voila_config)):
        return StreamingResponse(_get(fps_voila_handler, path))


@router.get("/")
async def get_root(voila_template: Optional[str] = None, voila_theme: Optional[str] = None, voila_config=Depends(get_voila_config)):
    fps_voila_handler.fps_arguments["voila-template"] = voila_template
    fps_voila_handler.fps_arguments["voila-theme"] = voila_theme
    path = voila_config.notebook_path or "/"
    if path == "/":
        return _get_tree(fps_voila_tree_handler, "/")
    else:
        return StreamingResponse(_get(fps_voila_handler, ""))

@router.get("/voila/render/{name}")
async def get_path(name):
    return _get_tree(fps_voila_tree_handler, name)

@router.get("/voila/tree{path:path}")
async def get_tree(path):
    return _get_tree(fps_voila_tree_handler, path)

@router.get("/voila/files/{path:path}")
def get_authorized_file(path):
    whitelisted = any(re.fullmatch(pattern, path) for pattern in CONFIG.whitelist)
    blacklisted = any(re.fullmatch(pattern, path) for pattern in CONFIG.blacklist)
    if not whitelisted:
        raise HTTPException(status_code=403, detail="File not whitelisted")
    if blacklisted:
        raise HTTPException(status_code=403, detail="File blacklisted")
    return _get_file(path)

@router.get("/voila/static/{path}")
def get_static_file(path):
    return _get_static_file(path)

@router.get("/voila/templates/lab/static/{path:path}")
def get_template_static_file(path):
    return _get_static_file(path)

def _get_static_file(path):
    for i, static_path in enumerate(fps_voila_handler.static_paths):
        file_path = Path(static_path) / path
        if os.path.exists(file_path):
            return _get_file(file_path)
    else:
        raise HTTPException(status_code=404, detail="File not found")

def _get_file(path):
    if os.path.exists(path):
        with open(path) as f:
            content = f.read()
        content_type, _ = guess_type(path)
        return Response(content, media_type=content_type)
    raise HTTPException(status_code=404, detail="File not found")

r = register_router(router)

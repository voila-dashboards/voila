import re
import os
from pathlib import Path
from http import HTTPStatus
from typing import Optional

from voila.handler import _VoilaHandler, _get
from voila.treehandler import _VoilaTreeHandler, _get as _get_tree
from voila.paths import collect_static_paths
from nbclient.util import ensure_async

from mimetypes import guess_type
from starlette.requests import Request
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse, StreamingResponse, HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
from fps.hooks import register_router  # type: ignore


class Config:
    pass

C = Config()

class WhiteListFileHandler:
    pass

white_list_file_handler = WhiteListFileHandler()

class FPSVoilaTreeHandler(_VoilaTreeHandler):
    is_fps = True
    request = Config()

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
    request = Config()
    fps_arguments = {}
    html = []

    def redirect(self, url):
        return RedirectResponse(url)

    def get_argument(self, name, default):
        if self.fps_arguments.get(name) is None:
            return default
        return self.fps_arguments[name]


fps_voila_handler = FPSVoilaHandler()
fps_voila_tree_handler = FPSVoilaTreeHandler()

def init_fps(
    *,
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
    white_list_file_handler.whitelist = whitelist
    white_list_file_handler.blacklist = blacklist
    white_list_file_handler.path = root_dir

    kwargs = {
        "template_paths": template_paths,
        "traitlet_config": config,
        "voila_configuration": voila_configuration,
    }
    if notebook_path:
        kwargs["notebook_path"] = os.path.relpath(notebook_path, root_dir)

    fps_voila_handler.initialize(**kwargs)
    fps_voila_handler.root_dir = root_dir
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

    C.notebook_path = notebook_path
    C.root_dir = root_dir


router = APIRouter()

@router.post("/voila/api/shutdown/{kernel_id}", status_code=204)
async def shutdown_kernel(kernel_id):
    await ensure_async(fps_voila_handler.kernel_manager.shutdown_kernel(kernel_id))
    return Response(status_code=HTTPStatus.NO_CONTENT.value)

@router.get("/notebooks/{path:path}")
async def get_root(path, voila_template: Optional[str] = None, voila_theme: Optional[str] = None):
    fps_voila_handler.request.query = request.query_params
    fps_voila_handler.request.path = request.url.path
    fps_voila_handler.request.host = f"{request.url.hostname}:{request.url.port}"
    fps_voila_handler.request.headers = request.headers
    return StreamingResponse(_get(fps_voila_handler, path))

@router.get("/")
async def get_root(request: Request, voila_template: Optional[str] = None, voila_theme: Optional[str] = None):
    fps_voila_handler.fps_arguments["voila-template"] = voila_template
    fps_voila_handler.fps_arguments["voila-theme"] = voila_theme
    path = fps_voila_handler.notebook_path or "/"
    if path == "/":
        if C.notebook_path:
            raise HTTPException(status_code=404, detail="Not found")
        else:
            fps_voila_tree_handler.request.path = request.url.path
            return _get_tree(fps_voila_tree_handler, "/")
    else:
        fps_voila_handler.request.query = request.query_params
        fps_voila_handler.request.path = request.url.path
        fps_voila_handler.request.host = f"{request.url.hostname}:{request.url.port}"
        fps_voila_handler.request.headers = request.headers
        return StreamingResponse(_get(fps_voila_handler, ""))

@router.get("/voila/render/{path:path}")
async def get_path(request: Request, path):
    if C.notebook_path:
        raise HTTPException(status_code=404, detail="Not found")
    else:
        fps_voila_handler.request.query = request.query_params
        fps_voila_handler.request.path = request.url.path
        fps_voila_handler.request.host = f"{request.url.hostname}:{request.url.port}"
        fps_voila_handler.request.headers = request.headers
        return StreamingResponse(_get(fps_voila_handler, path))

@router.get("/voila/tree{path:path}")
async def get_tree(request: Request, path):
    if C.notebook_path:
        raise HTTPException(status_code=404, detail="Not found")
    else:
        fps_voila_tree_handler.request.path = request.url.path
        return _get_tree(fps_voila_tree_handler, path)

# WhiteListFileHandler
@router.get("/voila/files/{path:path}")
def get_whitelisted_file(path):
    whitelisted = any(re.fullmatch(pattern, path) for pattern in white_list_file_handler.whitelist)
    blacklisted = any(re.fullmatch(pattern, path) for pattern in white_list_file_handler.blacklist)
    if not whitelisted:
        raise HTTPException(status_code=403, detail="File not whitelisted")
    if blacklisted:
        raise HTTPException(status_code=403, detail="File blacklisted")
    return _get_file(path, in_dir=white_list_file_handler.path)

@router.get("/voila/static/{path}")
def get_static_file(path):
    return _get_file_in_dirs(path, fps_voila_handler.static_paths)

@router.get("/voila/templates/{path:path}")
def get_template_file(path):
    template, static, relpath = os.path.normpath(path).split(os.path.sep, 2)
    assert static == "static"
    roots = collect_static_paths(["voila", "nbconvert"], template)
    for root in roots:
        abspath = os.path.abspath(os.path.join(root, relpath))
        if os.path.exists(abspath):
            return _get_file(abspath)
            break
    raise HTTPException(status_code=404, detail="File not found")

def _get_file_in_dirs(path, dirs):
    for d in dirs:
        p = Path(d) / path
        if p.is_file():
            return _get_file(p)
    else:
        raise HTTPException(status_code=404, detail="File not found")

def _get_file(path: str, in_dir: Optional[str] = None):
    if in_dir is None:
        p = Path(path)
    else:
        p = Path(in_dir) / path
    if p.is_file():
        with open(p) as f:
            content = f.read()
        content_type, _ = guess_type(p)
        return Response(content, media_type=content_type)
    raise HTTPException(status_code=404, detail="File not found")

r = register_router(router)

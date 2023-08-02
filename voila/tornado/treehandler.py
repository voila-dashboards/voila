#############################################################################
# Copyright (c) 2018, Voilà Contributors                                    #
# Copyright (c) 2018, QuantStack                                            #
#                                                                           #
# Distributed under the terms of the BSD 3-Clause License.                  #
#                                                                           #
# The full license is in the file LICENSE, distributed with this software.  #
#############################################################################
import os

from jupyter_server.utils import url_escape, url_path_join
from jupyter_core.utils import ensure_async
from tornado import web

from ..treehandler import VoilaTreeHandler
from ..utils import get_page_config, get_server_root_dir


class TornadoVoilaTreeHandler(VoilaTreeHandler):
    @web.authenticated
    async def get(self, path=""):
        cm = self.contents_manager
        dir_exists = await ensure_async(cm.dir_exists(path=path))
        file_exists = await ensure_async(cm.file_exists(path))
        if dir_exists:
            is_hidden = await ensure_async(cm.is_hidden(path))
            if is_hidden and not cm.allow_hidden:
                self.log.info("Refusing to serve hidden directory, via 404 Error")
                raise web.HTTPError(404)
            breadcrumbs = self.generate_breadcrumbs(path)
            page_title = self.generate_page_title(path)
            contents = await ensure_async(cm.get(path))

            def allowed_content(content):
                if content["type"] in ["directory", "notebook"]:
                    return True
                __, ext = os.path.splitext(content.get("path"))
                return ext in self.allowed_extensions

            contents["content"] = sorted(contents["content"], key=lambda i: i["name"])
            contents["content"] = filter(allowed_content, contents["content"])

            theme_arg = (
                self.get_argument("theme", self.voila_configuration.theme)
                if self.voila_configuration.allow_theme_override == "YES"
                else self.voila_configuration.theme
            )
            page_config = get_page_config(
                base_url=self.base_url,
                settings=self.settings,
                log=self.log,
                voila_configuration=self.voila_configuration,
            )
            page_config["jupyterLabTheme"] = theme_arg

            self.write(
                self.render_template(
                    "tree.html",
                    frontend="voila",
                    main_js="voila.js",
                    page_title=page_title,
                    notebook_path=path,
                    breadcrumbs=breadcrumbs,
                    contents=contents,
                    terminals_available=False,
                    server_root=get_server_root_dir(self.settings),
                    query=self.request.query,
                    page_config=page_config,
                )
            )
        elif file_exists:
            # it's not a directory, we have redirecting to do
            model = await ensure_async(cm.get(path, content=False))
            # redirect to /api/notebooks if it's a notebook, otherwise /api/files
            service = "notebooks" if model["type"] == "notebook" else "files"
            url = url_path_join(
                self.base_url,
                service,
                url_escape(path),
            )
            self.log.debug("Redirecting %s to %s", self.request.path, url)
            self.redirect(url)
        else:
            raise web.HTTPError(404)

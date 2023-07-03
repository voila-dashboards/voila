from jupyterlab_server.settings_handler import SettingsHandler
from tornado import web


class VoilaSettingHandler(SettingsHandler):
    """A settings API handler."""

    @web.authenticated
    def put(self, schema_name):
        self.set_status(404)

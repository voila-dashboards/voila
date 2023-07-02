import json
from typing import List
import tornado
from jupyter_server.base.handlers import APIHandler
from pathlib import Path

with open(Path(__file__).parent / "all.json", "r") as f:
    ALL_SCHEMA: List = json.load(f)


class VoilaSettingHandler(APIHandler):
    @tornado.web.authenticated
    def get(self, schema_name=""):
        """
        Get setting(s)

        Parameters
        ----------
        schema_name: str
            The id of a unique schema to send, added to the URL
        """
        # Need to be update here as translator locale is not change when a new locale is put
        # from frontend
        if schema_name != "":
            schemas = [x for x in ALL_SCHEMA if x["id"] == schema_name]
            if len(schemas) > 0:
                response = schemas[0]
            else:
                response = {}
        else:
            response = ALL_SCHEMA

        return self.finish(json.dumps(response))

    @tornado.web.authenticated
    def put(self, schema_name):
        """Update a setting"""
        self.set_status(204)

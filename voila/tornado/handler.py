#############################################################################
# Copyright (c) 2018, Voilà Contributors                                    #
# Copyright (c) 2018, QuantStack                                            #
#                                                                           #
# Distributed under the terms of the BSD 3-Clause License.                  #
#                                                                           #
# The full license is in the file LICENSE, distributed with this software.  #
#############################################################################
import tornado.web

from ..handler import VoilaHandler


class TornadoVoilaHandler(VoilaHandler):
    @tornado.web.authenticated
    async def get(self, path=None):
        gen = self.get_generator(path=path)
        async for html in gen:
            self.write(html)
            self.flush()

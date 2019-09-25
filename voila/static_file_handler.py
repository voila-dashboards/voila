#############################################################################
# Copyright (c) 2018, Voila Contributors                                    #
# Copyright (c) 2018, QuantStack                                            #
#                                                                           #
# Distributed under the terms of the BSD 3-Clause License.                  #
#                                                                           #
# The full license is in the file LICENSE, distributed with this software.  #
#############################################################################

import os
import re

import tornado.web


class MultiStaticFileHandler(tornado.web.StaticFileHandler):
    """A static file handler that 'merges' a list of directories

    If initialized like this::

        application = web.Application([
            (r"/content/(.*)", web.MultiStaticFileHandler, {"paths": ["/var/1", "/var/2"]}),
        ])

    A file will be looked up in /var/1 first, then in /var/2.

    """

    def initialize(self, paths, default_filename=None):
        self.roots = paths
        super(MultiStaticFileHandler, self).initialize(path=paths[0], default_filename=default_filename)

    def get_absolute_path(self, root, path):
        # find the first absolute path that exists
        self.root = self.roots[0]
        for root in self.roots:
            abspath = os.path.abspath(os.path.join(root, path))
            if os.path.exists(abspath):
                self.root = root  # make sure all the other methods in the base class know how to find the file
                break
        return abspath


class WhiteListFileHandler(tornado.web.StaticFileHandler):
    def initialize(self, whitelist=[], blacklist=[], **kwargs):
        self.whitelist = whitelist
        self.blacklist = blacklist
        super(WhiteListFileHandler, self).initialize(**kwargs)

    def get_absolute_path(self, root, path):
        # StaticFileHandler.get always calls this method first, so we use this as the
        # place to check the path. Note that now the path seperator is os dependent (\\ on windows)
        whitelisted = any(re.fullmatch(pattern, path) for pattern in self.whitelist)
        blacklisted = any(re.fullmatch(pattern, path) for pattern in self.blacklist)
        if not whitelisted:
            raise tornado.web.HTTPError(403, 'File not whitelisted')
        if blacklisted:
            raise tornado.web.HTTPError(403, 'File blacklisted')
        return super(WhiteListFileHandler, self).get_absolute_path(root, path)

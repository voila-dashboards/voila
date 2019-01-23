import os

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

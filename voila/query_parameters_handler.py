from tornado.web import RequestHandler


class QueryParametersHandler(RequestHandler):

    def initialize(self, kernel_manager=None):
        self._kernel_manager = None
        if hasattr(kernel_manager, 'get_query_params'):
            self._kernel_manager = kernel_manager

    async def get(self, kernel_id: str, var_name: str):
        if self._kernel_manager is not None:
            content = self._kernel_manager.get_query_params(kernel_id, var_name)
            self.finish(content[0])
        else:
            self.finish(None)

import aiohttp
from aiohttp import web
from .search import searchapp

apiapp_routes = web.RouteTableDef()
apiapp = web.Application()
apiapp.add_subapp('/search', searchapp)

@apiapp_routes.view('', name='api')
class Api(web.View):
    """
    Search packages within singularity containers
    """
    @classmethod
    def gen_docstring(cls):
        # TODO can I get searchapp automatically?
        # Turn this into a library if you can
        routes = {route.get_info()['path']: route.handler.gen_docstring() for router_name in searchapp.router for route in searchapp.router[router_name]._routes}
        doc = "{doc}\n{routes}".format(doc=cls.__doc__, routes='\n\n'.join(['{path}:\n{doc}'.format(path=key, doc=value) for key, value in routes.items()]))
        return doc

    async def get(self):
        """
        Get some text
        """
        return web.Response(text=self.gen_docstring())

apiapp.add_routes(apiapp_routes)

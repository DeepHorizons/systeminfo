import asyncio
import aiohttp
from aiohttp import web
import aiohttp_jinja2
import jinja2
from api import apiapp
from api.search import Search
from gen_images import generate_images

async def on_prepare(app):
    app.logger.info("Startup: Creating image...")
    data = await generate_images(app)
    app['images'] = data
    app.logger.info("Startup: Finished creating images")

def create_app(argv=''):
    """
    Create and return the aiohttp app
    Used for `adev runserver`
    """
    app = web.Application()
    aiohttp_jinja2.setup(app,
        loader=jinja2.FileSystemLoader('.'))
    app.add_routes([web.get('/', Search)])
    app.add_subapp('/api', apiapp)
    app.on_startup.append(on_prepare)
    return app

if __name__ == '__main__':
    app = create_app()
    web.run_app(app)

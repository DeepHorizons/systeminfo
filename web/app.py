import asyncio
import datetime
import aiohttp
from aiohttp import web
import aiohttp_jinja2
import jinja2
from api import apiapp
from api.search import Search
from gen_images import generate_images


async def update_images_periodically(app, timedelta=datetime.timedelta(minutes=5)):
    app.logger.critical("Starting search image task")
    try:
        while True:
            start = datetime.datetime.now()
            next = start + timedelta
            app.logger.info("Starting image check at `{start}`".format(start=start))
            data = await generate_images(app)
            app['images'] = data

            end = datetime.datetime.now()
            duration = (end - start).total_seconds()
            diff = next - end
            next_check = diff.total_seconds()
            app.logger.info("Finished in `{duration}` s, next in check in `{next_check}` s".format(duration=duration, next_check=next_check))
            if next_check >= 0:
                await asyncio.sleep(next_check)
    except asyncio.CancelledError:
        pass


async def start_background_tasks(app):
    app['background_image_watcher'] = app.loop.create_task(update_images_periodically(app))

async def cleanup_background_tasks(app):
    app['background_image_watcher'].cancel()
    await app['background_image_watcher']



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
    app.on_startup.append(start_background_tasks)
    app.on_cleanup.append(cleanup_background_tasks)
    return app

if __name__ == '__main__':
    app = create_app()
    web.run_app(app)

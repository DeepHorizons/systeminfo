import asyncio
import time
import os
import sys
import os
import systeminfo

async def generate_images(app):
    """
    This function creates and initalizes info objects that will be used for
    the web server
    
    This function should be changed to fit your needs
    """
    if 'SINGULARITY_IMAGE_DIR' in os.environ:
        data = singularity_images(os.environ['SINGULARITY_IMAGE_DIR'])
    else:
        app.logger.warning("SINGULARITY_IMAGE_DIR envvar not set; Using local system info")
        data = local_test()
    app.logger.info(data)
    app.logger.debug("getting data for {len} images".format(len=len(data)))
    
    # Async worked much better here, 10 images took about 120 seconds using sync, 50 seconds using async
    start = time.time()
    await asyncio.gather(*[info.async_get_dict() for info in data.values()])
    end = time.time()
    app.logger.debug("Took {seconds} seconds".format(seconds=end-start))
    return data

def local_test(num=1):
    return {image_name: systeminfo.System() for image_name in ('localhost' + str(i) for i in range(num))}

def singularity_images(path):
    # Find all images, symlink and all
    images = [os.path.join(path, file) for path, folers, files in os.walk(path) for file in files if file.endswith('img')]
    images.sort(key=lambda key: len(key))
    # TODO Get hashes of each
    # TODO Compare against previous under app['singularity_images']
    # TODO Report new images, deleted images, and changed hash values
    # Create a Singularity info for every image
    data = {image_name: systeminfo.Singularity(image_name) for image_name in images}
    return data

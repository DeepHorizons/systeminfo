import asyncio
import time
import os
import sys
import systeminfo

async def generate_images(app):
    """
    This function creates and initalizes info objects that will be used for
    the web server
    
    This function should be changed to fit your needs
    """
    data = local_test()
    app.logger.debug("getting data for {len} images".format(len=len(data)))
    
    # Async worked much better here, 10 images took about 120 seconds using sync, 50 seconds using async
    start = time.time()
    await asyncio.gather(*[info.async_get_dict() for info in data.values()])
    end = time.time()
    app.logger.debug("Took {seconds} seconds".format(seconds=end-start))
    return data

def local_test(num=1):
    return {image_name: systeminfo.System() for image_name in ('localhost' + str(i) for i in range(num))}

def singularity_images():
    # Find all images, symlink and all
    images = [os.path.join(path, file) for path, folers, files in os.walk('/opt/singularity/images') for file in files]
    images.sort(key=lambda key: len(key))
    # TODO Get hashes of each
    # TODO Compare against previous under app['singularity_images']
    # TODO Report new images, deleted images, and changed hash values
    # Create a Singularity info for every image
    data = {image_name: systeminfo.Singularity(image_name) for image_name in images}
    return data
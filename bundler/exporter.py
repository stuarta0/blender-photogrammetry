import bpy
import os
import shutil
from math import floor
from pprint import pprint

def convert_image(filepath, target):
    """ Creates a scene specifically for saving an image as JPG """
    sc = bpy.data.scenes.new('photogrammetry_helper')
    try:
        img = bpy.data.images.load(filepath)
        r = sc.render
        r.resolution_x = img.size[0]
        r.resolution_y = img.size[1]
        r.resolution_percentage = floor(100 * min(1.0, (3000 / max(r.resolution_x, r.resolution_y))))  # 3000px limit on PMVS
        r.image_settings.file_format = 'JPEG'
        r.image_settings.quality = 100

        sc.display_settings.display_device = 'sRGB'
        img.save_render(target, scene=sc)
        bpy.data.images.remove(img)
    finally:
        # remove the temporary export scene
        bpy.data.scenes.remove(sc)


def load(properties, data, *args, **kwargs):
    """
    Takes the structure calculated from parsing the input and writes to the bundler file structure
    """
    dirpath = bpy.path.abspath(properties.dirpath)

    cameras = data['cameras']
    camera_keys = list(cameras.keys())
    trackers = data['trackers']

    if not os.path.exists(dirpath):
        os.makedirs(dirpath)

    # copy and convert all images into bundler folder
    for idx, key in enumerate(camera_keys):
        camera = cameras[key]
        filepath = camera['filename']
        target = os.path.join(dirpath, os.path.splitext(os.path.basename(filepath))[0] + '.jpg')
        convert_image(filepath, target)
        #shutil.copy(camera['filename'], dirpath)
        camera['filename'] = os.path.basename(target)

    # write the image list file that corresponds with the camera index in bundle.out
    with open(os.path.join(dirpath, 'list.txt'), 'w+') as f:
        f.writelines(['{}\n'.format(camera['filename']) for id, camera in cameras.items()])

    # now write the bundle file
    sift = 0
    with open(os.path.join(dirpath, 'bundle.out'), 'w+') as f:
        f.write('# Bundle file v0.3\n')
        f.write('{} {}\n'.format(len(cameras.items()), len(trackers.items())))
        for idx, key in enumerate(camera_keys):
            camera = cameras[key]
            f.write('{f} {k[0]} {k[1]}\n'.format(**camera))
            f.write('{} {} {}\n'.format(*camera['R'][0]))
            f.write('{} {} {}\n'.format(*camera['R'][1]))
            f.write('{} {} {}\n'.format(*camera['R'][2]))
            f.write('{} {} {}\n'.format(*camera['t']))
        
        # now write the points and corresponding matching cameras
        for tid, track in trackers.items():
            f.write('{} {} {}\n'.format(*track['co']))
            f.write('{} {} {}\n'.format(*track['rgb']))
            # calculate view list
            visible_in = {}
            for key, camera in cameras.items():
                if tid in camera['trackers']:
                    visible_in[key] = camera['trackers'][tid]  # visible_in[camera 4]: (x, y)
            
            f.write('{count}'.format(count=len(visible_in.items())))
            for camera_key, co in visible_in.items():
                # The pixel positions are floating point numbers in a coordinate system where the origin is the center of the image, 
                # the x-axis increases to the right, and the y-axis increases towards the top of the image. Thus, (-w/2, -h/2) is 
                # the lower-left corner of the image, and (w/2, h/2) is the top-right corner (where w and h are the width and height of the image).
                # http://www.cs.cornell.edu/~snavely/bundler/bundler-v0.4-manual.html
                f.write(' {idx} {sift} {co[0]} {co[1]}'.format(
                    idx=camera_keys.index(camera_key),
                    sift=sift,
                    co=co,))
                sift += 1
            f.write('\n')

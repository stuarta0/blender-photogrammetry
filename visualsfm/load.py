import bpy
import os
import shutil
from math import floor, pi
from mathutils import Vector, Matrix, Quaternion, Euler
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
    Takes the structure calculated from parsing the input and writes to the NVM file structure
    """
    dirpath = bpy.path.abspath(properties.dirpath)
    if not dirpath:
        raise AttributeError('VisualSfM Workspace Directory must be provided for output')

    cameras = data['cameras']
    camera_keys = list(cameras.keys())
    trackers = data['trackers']

    if not os.path.exists(dirpath):
        os.makedirs(dirpath)

    # copy and convert all images into visualsfm folder
    for idx, key in enumerate(camera_keys):
        camera = cameras[key]
        filepath = camera['filename']
        target = os.path.join(dirpath, os.path.splitext(os.path.basename(filepath))[0] + '.jpg')
        convert_image(filepath, target)
        #shutil.copy(camera['filename'], dirpath)
        camera['filename'] = os.path.basename(target)

    # now write the nvm file
    with open(os.path.join(dirpath, 'bundle.nvm'), 'w+') as f:
        f.write('NVM_V3\n\n')
        f.write(f'{len(cameras.items())}\n')
        for idx, key in enumerate(camera_keys):
            camera = cameras[key]

            # transform camera extrinsics appropriately
            R = Matrix(camera['R'])
            R.transpose()
            c = Vector(camera['t'])
            t = -1 * R @ c
            R.transpose()
            R.rotate(Euler((pi, 0, 0)))

            # TODO: confirm whether the distortion coefficient needs inverting
            # <Camera> = <File name> <focal length> <quaternion WXYZ> <camera center> <radial distortion> 0
            f.write('{filename} {f} {q[0]} {q[1]} {q[2]} {q[3]} {t[0]} {t[1]} {t[2]} {k[0]} 0\n'.format(
                filename=camera['filename'],
                f=camera['f'],
                q=R.to_quaternion(),
                t=t,
                k=camera['k']))
        
        # now write the points and corresponding matching cameras
        f.write(f'\n{len(trackers.items())}\n')
        sift = 0
        for tid, track in trackers.items():
            # <Point> = <XYZ> <RGB> <number of measurements> <List of Measurements>
            # <Measurement> = <Image index> <Feature Index> <xy>
            measurements = {}
            for cid, camera in cameras.items():
                if tid in camera['trackers']:
                    measurements.setdefault(cid, camera['trackers'][tid])
            
            f.write('{co[0]} {co[1]} {co[2]} {rgb[0]} {rgb[1]} {rgb[2]} {num_measurements}'.format(**track, num_measurements=len(measurements.items())))
            for cid, measurement in measurements.items():
                f.write(' {image_idx} {feature_idx} {x} {y}'.format(image_idx=cid,
                                                                    feature_idx=sift,
                                                                    x=measurement[0],
                                                                    y=-1 * measurement[1]))
                sift += 1
            f.write('\n')

        f.write('\n\n\n0\n\n')
        f.write('#the last part of NVM file points to the PLY files\n')
        f.write('#the first number is the number of associated PLY files\n')
        f.write('#each following number gives a model-index that has PLY\n')
        f.write('0\n')

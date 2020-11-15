import bpy
import os
# from lxml import etree as ET
import xml.etree.ElementTree as ET
from math import tan, radians
from mathutils import Vector, Matrix, Euler
from ..utils import get_image_size


def extract(properties, *args, **kwargs):
    """
    :returns: {
        'resolution': (width, height),
        'trackers': { 
            int: (x, y, z),
        },
        'cameras': {
            int: {
                'filename': str,
                'f': float,
                'k': (k1, k2, k3),
                'c': (x, y, z),  # real world coord
                't': (x, y, z),  # pmvs transformed translation
                'R': ((r00, r01, r02),
                        (r10, r11, r12),
                        (r20, r21, r22)),
                'trackers': {
                    int: (x, y),
                }
            }
        }
    }
    """
    filename = bpy.path.abspath(properties.filepath)
    imagepaths = list(filter(None, bpy.path.abspath(properties.imagepath).split(';')))
    if not os.path.exists(filename):
        if not filename:
            raise AttributeError(f'ImageModeler filepath must be provided')
        raise AttributeError(f'Unable to locate ImageModeler file:\n"{filename}"')

    data = {
        'trackers': {},
        'cameras': {},
    }
    doc = ET.parse(filename)
    for locator in doc.findall('L'):
        co = locator.find('P').attrib
        data['trackers'][int(locator.attrib['i'])] = {
            'co': (float(co['x']), float(co['y']), float(co['z'])),
            'rgb': (0, 0, 0),
        }
    
    cinfs = {}
    for cinf in doc.findall('CINF'):
        cinfs[cinf.attrib['i']] = cinf.attrib
    # cinf = doc.find('CINF').attrib

    for shot in doc.findall('SHOT'):
        cfrm = shot.find('CFRM')

        # test data indicates frame wasn't matched if cfrm doesn't reference a camera
        if 'cf' not in cfrm.attrib:
            continue
        
        cinf = cinfs.get(cfrm.attrib['cf'], {})
        intrinsics = cfrm.attrib
        intrinsics.setdefault('rd', cinf.get('rd', 0))
        extrinsics = {
            'T': cfrm.find('T').attrib,
            'R': cfrm.find('R').attrib
        }
        
        extrinsics.update({
            'T': Vector((float(extrinsics['T']['x']), float(extrinsics['T']['y']), float(extrinsics['T']['z']))),
            'R': Euler((radians(float(extrinsics['R']['x'])),
                        radians(float(extrinsics['R']['y'])), 
                        radians(float(extrinsics['R']['z']))), 'XYZ').to_matrix()
        })
        extrinsics['R'].transpose()

        # pinhole camera model
        # https://photo.stackexchange.com/a/41280
        # FOV = 2 * atan((sensor_width / 2) / focal_length)
        # focal_length = (sensor_width / 2) / tan(FOV / 2)
        f = (float(cinf['fbw']) / 2) / tan(radians(float(intrinsics['fovx']) / 2))
        f_pixels = int(shot.attrib['w']) * (f / float(cinf['fbw']))

        # find any filename that exists
        filenames = [fp for fp in [os.path.join(*parts) for parts in zip(imagepaths, [shot.attrib['n'],] * len(imagepaths))] if os.path.exists(fp)]
        if not filenames:
            # wasn't in a root path, do we search sub directories?
            if properties.subdirs:
                for imagepath in imagepaths:
                    for root, dirs, files in os.walk(imagepath):
                        if shot.attrib['n'] in files:
                            filenames = [os.path.join(root, shot.attrib['n'])]

            # still didn't find file?
            if not filenames:
                raise AttributeError(f'ImageModeler image not found for camera "{shot.attrib["i"]}":\n"{shot.attrib["n"]}"')

        camera = data['cameras'].setdefault(int(shot.attrib['i']), {
            'filename': filenames[0],
            'f': f_pixels,
            'k': (-float(intrinsics['rd']),) * 3,
            'c': extrinsics['T'],
            'R': tuple(map(tuple, tuple(extrinsics['R']))),
            't': tuple(-1 * extrinsics['R'] @ extrinsics['T']),
        })

        if 'resolution' not in data:
            data.setdefault('resolution', get_image_size(camera['filename']))

        trackers = camera.setdefault('trackers', {})
        for marker in shot.find('IPLN').find('IFRM').findall('M'):
            trackers[int(marker.attrib['i'])] = (float(marker.attrib['x']), float(marker.attrib['y']))

    return data


# def convert_images(self, data, out_dir):
#     """
#     Convert all images in the camera data to jpeg
#     """
#     def get_filename(source):
#         name = os.path.basename(source)
#         name, ext = os.path.splitext(name)
#         return os.path.join(out_dir, '{name}.jpg'.format(name=name))

#     for camera in data['cameras'].values():
#         filename = camera['filename']
#         out = get_filename(filename)
#         print('Converting {} to {}'.format(filename, out))
#         if not os.path.exists(out):
#             print('opening image')
#             orig = Image.open(filename)
#             print('creating new image')
#             im = Image.new('RGB', orig.size, (255,)*3)
#             print('pasting image')
#             im.paste(orig, (0,0))
#             print('saving image')
#             try:
#                 im.save(out, quality=95)
#             except Exception as ex:
#                 print(ex)
#         else:
#             print('image exists')
#         camera['filename'] = os.path.basename(out)

import bpy
import os
# from lxml import etree as ET
import xml.etree.ElementTree as ET
from math import tan, radians
from mathutils import Vector, Matrix, Euler


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

    # TODO: load first referenced image in bpy.data and get size
    # img = bpy.data.images.load(os.path.join(os.path.dirname(imagepath), filepath))
    # 'resolution': img.size
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
    
    cinf = doc.find('CINF').attrib

    for shot in doc.findall('SHOT'):
        cfrm = shot.find('CFRM')
        intrinsics = cfrm.attrib
        extrinsics = {
            'T': cfrm.find('T').attrib,
            'R': cfrm.find('R').attrib
        }
        
        # Z rotation in blender is based on Y being 0
        # Z rotation from IM assumes X is 0 like in all standard maths
        # transform Z rotation to blenders representation by subtracting 90 degrees
        z = float(extrinsics['R']['z'])
        extrinsics.update({
            'T': Vector((float(extrinsics['T']['x']), float(extrinsics['T']['y']), float(extrinsics['T']['z']))),
            'R': Euler((radians(float(extrinsics['R']['x'])),
                        radians(float(extrinsics['R']['y'])), 
                        radians(z)), 'XYZ').to_matrix()
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
            raise Exception('Image not found for camera {}: {}'.format(shot.attrib['i'], shot.attrib['n']))

        camera = data['cameras'].setdefault(int(shot.attrib['i']), {
            'filename': filenames[0],
            'f': f_pixels,
            'k': (-float(intrinsics['rd']),) * 3,
            'c': extrinsics['T'],
            'R': tuple(map(tuple, tuple(extrinsics['R']))),
            't': tuple(-1 * extrinsics['R'] * extrinsics['T']),
        })

        if 'resolution' not in data:
            img = bpy.data.images.load(camera['filename'])
            data.setdefault('resolution', tuple(img.size))
            bpy.data.images.remove(img)

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

import os
import re
import subprocess
import shutil
import platform

import bpy

from ..bundler.load import load as load_bundler
from ..utils import set_active_collection, get_binpath_for_module, get_binary_path


class BundlerProperties(object):
    def __init__(self, dirpath, *args, **kwargs):
        super()
        self.dirpath = dirpath


def prepare_workspace(properties, data):
    """
    Prepares a PMVS workspace.
    :returns: Path to the PMVS options file
    """
    dirpath = bpy.path.abspath(properties.dirpath)
    binpath = get_binpath_for_module(os.path.realpath(__file__))
    target = 'pmvs' + os.sep

    # running PMVS requires transforming to Bundler first
    load_bundler(BundlerProperties(dirpath=dirpath), data)

    cwd = os.getcwd()
    try:
        os.chdir(dirpath)
        subprocess.call([get_binary_path(binpath, 'Bundle2PMVS'), 'list.txt', 'bundle.out', target, ])
        subprocess.call([get_binary_path(binpath, 'RadialUndistort'), 'list.txt', 'bundle.out', target, ])

        def mkdir(path):
            if not os.path.exists(path):
                os.mkdir(path)

        mkdir(os.path.join(target, 'models'))
        mkdir(os.path.join(target, 'txt'))
        mkdir(os.path.join(target, 'visualize'))

        with open(os.path.join(target, 'list.rd.txt'), 'r') as f:
            images = f.readlines()

        # copy 00000000.txt to txt\00000000.txt
        # copy image.rd.jpg to visualize\00000000.jpg

        # v0.3 format
        #int_format = '{:0>4}'

        # v0.4 format
        int_format = '{:0>8}'

        for i, path in enumerate(images):
            shutil.move(
                os.path.join(target, (int_format + '.txt').format(i)),
                os.path.join(target, 'txt', (int_format + '.txt').format(i)))
            shutil.move(
                os.path.join(target, '{}.rd.jpg'.format(os.path.basename(os.path.splitext(path)[0]))),
                os.path.join(target, 'visualize', (int_format + '.jpg').format(i)))

        # rewrite list.txt to include path to visualize\00000000.jpg
        with open(os.path.join(target, 'list.rd.txt'), 'w+') as f:
            f.writelines([('visualize\\' + int_format + '.jpg\n').format(i) for i, data in enumerate(images)])

        # rewrite pmvs_options.txt to skip vis.dat as we won't be using cmvs here
        pmvs_options = {
            'level': properties.level,
            'csize': properties.csize,
            'threshold': properties.threshold,
            'wsize': properties.wsize,
            'minImageNum': properties.minImageNum,
            'useVisData': 0,
        }
        pattern = re.compile(r'^([^\s]+)\s')
        with open(os.path.join(target, 'pmvs_options.txt'), 'r') as f:
            lines = f.readlines()
            for i, line in enumerate(lines):
                match = pattern.search(line)
                if match and match.group(1) in pmvs_options:
                    lines[i] = '{key} {value}\n'.format(key=match.group(1), value=pmvs_options[match.group(1)])
        
        os.chdir(target)
        options_path = 'reconstruction'
        with open(options_path, 'w+') as f:
            f.writelines(lines)

        return os.path.join(dirpath, target, options_path)

    finally:
        os.chdir(cwd)

# https://www.di.ens.fr/pmvs/documentation.html
def load(properties, data, *args, **kwargs):
    options_path = prepare_workspace(properties, data)
    os.chdir(os.path.dirname(options_path))
    
    binpath = get_binpath_for_module(os.path.realpath(__file__))
    subprocess.call([get_binary_path(binpath, 'pmvs2'), '.{}'.format(os.sep), os.path.basename(options_path), ])

    model = os.path.join('models', 'reconstruction.ply')
    if os.path.exists(model) and properties.import_points:
        set_active_collection(**kwargs)
        bpy.ops.import_mesh.ply(filepath=model)


# def create_debug_svg(bpy_module, bundle_path):
#     list_path = listpath_from_bundle(bundle_path)
#     with open(list_path, 'r') as f:
#         images = [{'filename': os.path.join(os.path.dirname(list_path), imagepath.strip()), 'points': []} for imagepath in f.readlines()]
#     img = bpy_module.data.images.load(images[0]['filename'])
#     width, height = img.size

#     with open(bundle_path, 'r') as f:
#         lines = f.readlines()

#     total_cameras, total_points = map(int, lines[1].split())
#     for i in range(total_points):
#         # each point uses 3 lines (3d point, rgb, view list)
#         idx = 2 + total_cameras * 5 + i * 3
#         view_list = lines[idx + 2].split()
#         length = int(view_list[0])
#         for p in range(length):
#             # <camera> <sift> <x> <y>
#             pdx = 1 + p * 4
#             images[int(view_list[pdx])]['points'].append((float(view_list[pdx + 2]), float(view_list[pdx + 3])))
    
#     debug_path = os.path.join(os.path.dirname(bundle_path), 'debug')
#     if not os.path.exists(debug_path):
#         os.mkdir(debug_path)

#     for image in images:
#         points = ['<circle cx="{x}" cy="{y}" r="5" fill="none" stroke="#f00" stroke-width="1"/>'.format(x=p[0]+width/2, y=height/2-p[1]) for p in image['points']]
#         with open(os.path.join(debug_path, os.path.splitext(os.path.basename(image['filename']))[0] + '.svg'), 'w+') as svg:
#             svg.write('''<svg width="{width}" height="{height}" version="1.1" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">
#     <image xlink:href="{filename}"/>
#     {points}
# </svg>'''.format(filename=image['filename'], width=width, height=height, points='\n\t'.join(points)))

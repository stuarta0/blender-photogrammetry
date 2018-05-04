import os
import re
import subprocess
import shutil
import platform


def listpath_from_bundle(bundle_path):
    name = '.'.join(['list',] + os.path.basename(bundle_path).split('.')[1:-1] + ['txt', ])
    return os.path.join(os.path.dirname(bundle_path), name)


def bundle2pmvs(bin_path, bundle_path, target_dir, pmvs_options):
    print('bundle2pmvs({}, {}, {})'.format(bin_path, bundle_path, target_dir))
    ext = '.exe' if platform.system().lower() == 'windows' else ''
    
    os.chdir(os.path.dirname(bundle_path))
    subprocess.call([os.path.join(bin_path, 'Bundle2PMVS{}'.format(ext)), 'list.txt', os.path.basename(bundle_path), target_dir, ])
    subprocess.call([os.path.join(bin_path, 'RadialUndistort{}'.format(ext)), 'list.txt', os.path.basename(bundle_path), target_dir, ])

    def mkdir(path):
        if not os.path.exists(path):
            os.mkdir(path)

    mkdir(os.path.join(target_dir, 'models'))
    mkdir(os.path.join(target_dir, 'txt'))
    mkdir(os.path.join(target_dir, 'visualize'))

    with open(os.path.join(target_dir, 'list.rd.txt'), 'r') as f:
        images = f.readlines()

    # copy 00000000.txt to txt\00000000.txt
    # copy image.rd.jpg to visualize\00000000.jpg

    # v0.3 format
    #int_format = '{:0>4}'

    # v0.4 format
    int_format = '{:0>8}'

    for i, path in enumerate(images):
        shutil.move(
            os.path.join(target_dir, (int_format + '.txt').format(i)),
            os.path.join(target_dir, 'txt', (int_format + '.txt').format(i)))
        shutil.move(
            os.path.join(target_dir, '{}.rd.jpg'.format(os.path.basename(os.path.splitext(path)[0]))),
            os.path.join(target_dir, 'visualize', (int_format + '.jpg').format(i)))

    # rewrite list.txt to include path to visualize\00000000.jpg
    with open(os.path.join(target_dir, 'list.rd.txt'), 'w+') as f:
        f.writelines([('visualize\\' + int_format + '.jpg\n').format(i) for i, data in enumerate(images)])

    # rewrite pmvs_options.txt to skip vis.dat as we won't be using cmvs here
    pmvs_options.update({'useVisData': 0})
    pattern = re.compile(r'^([^\s]+)\s')
    with open(os.path.join(target_dir, 'pmvs_options.txt'), 'r') as f:
        lines = f.readlines()
        for i, line in enumerate(lines):
            match = pattern.search(line)
            if match and match.group(1) in pmvs_options:
                lines[i] = '{key} {value}\n'.format(key=match.group(1), value=pmvs_options[match.group(1)])
    
    options = os.path.join(target_dir, 'reconstruction')
    with open(options, 'w+') as f:
        f.writelines(lines)
    return options


def pmvs(bin_path, option_path):
    # if linux, set:
    # LD_LIBRARY_PATH=/usr/lib/x86_64-linux-gnu:bin_path && export LD_LIBRARY_PATH
    print('pmvs({})'.format(option_path))
    os.chdir(os.path.dirname(option_path))

    ext = '.exe' if platform.system().lower() == 'windows' else ''
    subprocess.call([os.path.join(bin_path, 'pmvs2{}'.format(ext)), '.{}'.format(os.sep), os.path.basename(option_path), ])


def create_debug_svg(bpy_module, bundle_path):
    list_path = listpath_from_bundle(bundle_path)
    with open(list_path, 'r') as f:
        images = [{'filename': os.path.join(os.path.dirname(list_path), imagepath.strip()), 'points': []} for imagepath in f.readlines()]
    img = bpy_module.data.images.load(images[0]['filename'])
    width, height = img.size

    with open(bundle_path, 'r') as f:
        lines = f.readlines()

    total_cameras, total_points = map(int, lines[1].split())
    for i in range(total_points):
        # each point uses 3 lines (3d point, rgb, view list)
        idx = 2 + total_cameras * 5 + i * 3
        view_list = lines[idx + 2].split()
        length = int(view_list[0])
        for p in range(length):
            # <camera> <sift> <x> <y>
            pdx = 1 + p * 4
            images[int(view_list[pdx])]['points'].append((float(view_list[pdx + 2]), float(view_list[pdx + 3])))
    
    debug_path = os.path.join(os.path.dirname(bundle_path), 'debug')
    if not os.path.exists(debug_path):
        os.mkdir(debug_path)

    for image in images:
        points = ['<circle cx="{x}" cy="{y}" r="5" fill="none" stroke="#f00" stroke-width="1"/>'.format(x=p[0]+width/2, y=height/2-p[1]) for p in image['points']]
        with open(os.path.join(debug_path, os.path.splitext(os.path.basename(image['filename']))[0] + '.svg'), 'w+') as svg:
            svg.write('''<svg width="{width}" height="{height}" version="1.1" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">
    <image xlink:href="{filename}"/>
    {points}
</svg>'''.format(filename=image['filename'], width=width, height=height, points='\n\t'.join(points)))


def prepare():
    """
    :returns: {
        'trackers': { 
            id<int>: {
                'co': (x, y, z),
                'rgb': (r, g, b),
            }
        },
        'cameras': {
            id<int>: {
                'filename': str,
                'f': float,
                'k': (k1, k2, k3),
                'c': (x, y, z),  # real world coord
                't': (x, y, z),  # pmvs transformed translation
                'R': ((r00, r01, r02),
                      (r10, r11, r12),
                      (r20, r21, r22)),
                'trackers': {
                    id<int>: (x, y),
                }
            }
        }
    }
    """
    pass

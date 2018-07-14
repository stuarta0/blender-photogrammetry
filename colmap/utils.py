import os
import re
import subprocess
import shutil
import platform


colmap_path = ''

def colmap(command, args):
    print('colmap', command)
    subprocess.call([colmap_path, command, ] + [v for a in args for v in a])


def run_colmap(bin_path, database_path):
    print('run_colmap({})'.format(database_path))
    ext = '.bat' if platform.system().lower() == 'windows' else ''
    colmap_path = os.path.join(bin_path, 'COLMAP{}'.format(ext))

    dataset_path = os.path.dirname(database_path)
    os.mkdir(os.path.join(dataset_path, 'sparse'))
    os.mkdir(os.path.join(dataset_path, 'dense'))

    colmap('mapper', [
        ('--database_path', database_path),
        ('--image_path', os.path.join(dataset_path, 'images')),
        ('--export_path', os.path.join(dataset_path, 'sparse'))
    ])

    colmap('image_undistorter', [
        ('--image_path', os.path.join(dataset_path, 'images')),
        ('--input_path', os.path.join(dataset_path, 'sparse', '0')),
        ('--output_path', os.path.join(database_path, 'dense')),
        ('--output_type', 'COLMAP'),
        ('--max_image_size', '3000'),
    ])

    colmap('dense_stereo', [
        ('--workspace_path', os.path.join(dataset_path, 'dense')),
        ('--workspace_format', 'COLMAP'),
        ('--DenseSteroe.geom_consistency', 'true'),
    ])

    colmap('dense_fuser', [
        ('--workspace_path', os.path.join(dataset_path, 'dense')),
        ('--workspace_format', 'COLMAP'),
        ('--input_type', 'geometric'),
        ('--output_path', os.path.join(dataset_path, 'dense', 'fused.ply')),
    ])
    
    colmap('dense_mesher', [
        ('--input_path', os.path.join(dataset_path, 'dense', 'fused.ply')),
        ('--output_path', os.path.join(dataset_path, 'dense', 'meshed.ply')),
    ])

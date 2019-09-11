import os
import re
import subprocess
import shutil
import platform

import bpy
from math import pi
from mathutils import Matrix, Vector, Euler
from ..utils import get_binpath_for_module, get_binary_path


def interface_colmap(working_folder, input_file, output_file):
    """
    Import/export 3D reconstruction from/to COLMAP format as TXT (the only documented format).
    In order to import a scene, run COLMAP SfM and next undistort the images (only PINHOLE
    camera model supported for the moment); and convert the BIN scene to TXT by importing in
    COLMAP the sparse scene stored in 'dense' folder and exporting it as TXT.
    """
    binpath = get_binpath_for_module(os.path.realpath(__file__))
    exe = get_binary_path(binpath, 'InterfaceCOLMAP')
    args = [
        exe,
        '--working-folder', working_folder,
        '--input-file', input_file,
        '--output-file', output_file,
    ]
    print(' '.join(args))
    retcode = subprocess.call(args)
    if retcode != 0:
        raise Exception(f'openMVS {os.path.basename(exe)} failed, see system console for details')


def reconstruct_mesh(working_folder, input_file='scene.mvs', output_file='scene_mesh.mvs'):
    binpath = get_binpath_for_module(os.path.realpath(__file__))
    exe = get_binary_path(binpath, 'ReconstructMesh')
    args = [
        exe,
        '--working-folder', working_folder,
        '--input-file', input_file,
        '--output-file', output_file,
    ]
    print(' '.join(args))
    retcode = subprocess.call(args)
    if retcode != 0:
        raise Exception(f'openMVS {os.path.basename(exe)} failed, see system console for details')


def texture_mesh(working_folder, input_file='scene_mesh.mvs', output_file='scene_mesh_texture.obj', export_type='obj', empty_colour=None):
    binpath = get_binpath_for_module(os.path.realpath(__file__))
    exe = get_binary_path(binpath, 'TextureMesh')
    args = [
        exe,
        '--working-folder', working_folder,
        '--input-file', input_file,
        '--output-file', output_file,
        '--export-type', export_type,
    ]
    if empty_colour:
        try:
            # create a decimal from a collection of (r, g, b)
            empty_colour = (empty_colour[0] << 16) + (empty_colour[1] << 8) + empty_colour[2]
        except:
            pass

        try:
            args += ['--empty-color', str(int(empty_colour))]
        except:
            # empty colour wasn't a single integer value, skip
            pass
    
    print(' '.join(args))
    retcode = subprocess.call(args)
    if retcode != 0:
        raise Exception(f'openMVS {os.path.basename(exe)} failed, see system console for details')

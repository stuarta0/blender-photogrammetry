import os
import re
import subprocess
import shutil
import platform

import bpy
from math import pi
from mathutils import Matrix, Vector, Euler
from ..utils import get_binpath_for_module, get_binary_path


def interface_colmap(working_folder, input_file, output_file, execute=True):
    """
    Import/export 3D reconstruction from/to COLMAP format as TXT (the only documented format).
    In order to import a scene, run COLMAP SfM and next undistort the images (only PINHOLE
    camera model supported for the moment); and convert the BIN scene to TXT by importing in
    COLMAP the sparse scene stored in 'dense' folder and exporting it as TXT.

    If the OpenMVS binary InterfaceCOLMAP is not found, the command line will be replaced with
    $OPENMVS_INTERFACECOLMAP such that an environment variable could be used instead.
    :returns: The command line args that were executed (if execute=True).
    """
    binpath = get_binpath_for_module(os.path.realpath(__file__))
    exe = get_binary_path(binpath, 'InterfaceCOLMAP') or '$OPENMVS_INTERFACECOLMAP'
    args = [
        exe,
        '--working-folder', working_folder,
        '--input-file', input_file,
        '--output-file', output_file,
    ]
    print(' '.join(args))
    if execute:
        retcode = subprocess.call(args)
        if retcode != 0:
            raise Exception(f'openMVS {os.path.basename(exe)} failed, see system console for details')
    return args


def reconstruct_mesh(working_folder, input_file='scene.mvs', output_file='scene_mesh.mvs', execute=True):
    """
    If the OpenMVS binary ReconstructMesh is not found, the command line will be replaced with
    $OPENMVS_RECONSTRUCTMESH such that an environment variable could be used instead.
    :returns: The command line args that were executed (if execute=True).
    """
    binpath = get_binpath_for_module(os.path.realpath(__file__))
    exe = get_binary_path(binpath, 'ReconstructMesh') or '$OPENMVS_RECONSTRUCTMESH'
    args = [
        exe,
        '--working-folder', working_folder,
        '--input-file', input_file,
        '--output-file', output_file,
    ]
    print(' '.join(args))
    if execute:
        retcode = subprocess.call(args)
        if retcode != 0:
            raise Exception(f'openMVS {os.path.basename(exe)} failed, see system console for details')
    return args


def texture_mesh(working_folder, input_file='scene_mesh.mvs', output_file='scene_mesh_texture.obj', export_type='obj', empty_colour=None, execute=True):
    """
    If the OpenMVS binary TextureMesh is not found, the command line will be replaced with
    $OPENMVS_TEXTUREMESH such that an environment variable could be used instead.
    :returns: The command line args that were executed (if execute=True).
    """
    binpath = get_binpath_for_module(os.path.realpath(__file__))
    exe = get_binary_path(binpath, 'TextureMesh') or '$OPENMVS_TEXTUREMESH'
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
    if execute:
        retcode = subprocess.call(args)
        if retcode != 0:
            raise Exception(f'openMVS {os.path.basename(exe)} failed, see system console for details')
    return args

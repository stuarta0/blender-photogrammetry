import bpy
import os
import bmesh
from mathutils import Vector, Matrix


def load(properties, data, *args, **kwargs):
    """ Imports photogrammetry data into the current scene.
    """
    scene = kwargs.get('scene', None)
    if not scene:
        raise Exception('Scene required to load data in blender.load')


    if 'resolution' in data:
        scene.render.resolution_x, scene.render.resolution_y = data['resolution']

    for cid, camera in data['cameras'].items():
        # rotation in file needs to be transposed to work properly
        mrot = Matrix(camera['R'])
        mrot.transpose()
        rotation = mrot.to_euler('XYZ')

        # https://github.com/simonfuhrmann/mve/wiki/Math-Cookbook
        # t = -R * c
        # where c is the real world position as I've calculated, and t is the camera location stored in bundle.out
        translation = -1 * mrot * Vector(camera['t'])
        
        # create and link camera
        name = os.path.splitext(os.path.basename(camera['filename']))[0]
        cdata = bpy.data.cameras.new(name)
        cam = bpy.data.objects.new(name, cdata)
        scene.objects.link(cam)

        # set parameters
        cam.location = translation
        cam.rotation_euler = rotation
        cdata.sensor_width = 35
        cdata.lens = (camera['f'] * 35) / scene.render.resolution_x

    coords = []
    for tracker in data['trackers'].values():
        coords.append(Vector(tracker['co']))

    mesh = bpy.data.meshes.new("PhotogrammetryPoints")
    obj = bpy.data.objects.new("PhotogrammetryPoints", mesh)

    scene.objects.link(obj)
    scene.objects.active = obj 
    obj.select = True

    # add all coords from bundler points as vertices
    bm = bmesh.new()
    for v in coords:
        bm.verts.new(v)

    # make the bmesh the object's mesh
    bm.to_mesh(mesh)  
    bm.free()

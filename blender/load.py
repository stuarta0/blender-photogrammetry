import bpy
import os
import bmesh
from mathutils import Vector, Matrix


def load(properties, data, *args, **kwargs):
    """ Imports a scene in bundler format.
    :param bundle_path: the target bundle.out file
    :param list_path: the target list.txt file
    :param scene: the scene to import into
    """
    scene = kwargs.get('scene', None)
    if not scene:
        raise Exception('Scene required to load data in blender.load')

    if 'resolution' in data:
        scene.render.resolution_x, scene.render.resolution_y = data['resolution']

    for camera in data['cameras']:
        # rotation in file needs to be transposed to work properly
        mrot = Matrix(camera['R'])
        mrot.transpose()
        rotation = mrot.to_euler('XYZ')

        # https://github.com/simonfuhrmann/mve/wiki/Math-Cookbook
        # t = -R * c
        # where c is the real world position as I've calculated, and t is the camera location stored in bundle.out
        translation = -1 * mrot * camera['t']
        
        # create and link camera
        name = "BundlerCamera{}".format(i)
        data = bpy.data.cameras.new(name)
        cam = bpy.data.objects.new(name, data)
        scene.objects.link(cam)

        # set parameters
        cam.location = translation
        cam.rotation_euler = rotation
        data.sensor_width = 35
        data.lens = (camera['f'] * 35) / scene.render.resolution_x

    coords = []
    for tracker in data['trackers']:
        coords.append(Vector(tracker['co']))

    mesh = bpy.data.meshes.new("BundlerPoints")
    obj = bpy.data.objects.new("BundlerPoints", mesh)

    scene.objects.link(obj)
    scene.objects.active = obj 
    obj.select = True

    # mesh = bpy.context.object.data

    # add all coords from bundler points as vertices
    bm = bmesh.new()
    for v in coords:
        bm.verts.new(v)

    # make the bmesh the object's mesh
    bm.to_mesh(mesh)  
    bm.free()

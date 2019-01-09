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

    if 'resolution' in data and properties.update_render_size:
        scene.render.resolution_x, scene.render.resolution_y = data['resolution']

    for cid, camera in data['cameras'].items():
        # rotation in file needs to be transposed to work properly
        mrot = Matrix(camera['R'])
        mrot.transpose()
        rotation = mrot.to_euler('XYZ')

        # https://github.com/simonfuhrmann/mve/wiki/Math-Cookbook
        # t = -R * c
        # where c is the real world position as I've calculated, and t is the camera location stored in bundle.out
        translation = -1 * mrot @ Vector(camera['t'])
        
        # create and link camera
        name = os.path.splitext(os.path.basename(camera['filename']))[0]
        cdata = bpy.data.cameras.new(name)
        cam = bpy.data.objects.new(name, cdata)
        scene.collection.objects.link(cam)

        # add background images per camera!
        cdata.show_background_images = True
        bg = cdata.background_images.new()
        image_path = camera['filename']
        if properties.relative_paths:
            image_path = bpy.path.relpath(image_path)
        img = bpy.data.images.load(image_path)
        bg.image = img

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

    scene.collection.objects.link(obj)
    scene.view_layers[0].objects.active = obj
    obj.select_set(True)

    # add all coords from bundler points as vertices
    bm = bmesh.new()
    for v in coords:
        bm.verts.new(v)

    # make the bmesh the object's mesh
    bm.to_mesh(mesh)  
    bm.free()

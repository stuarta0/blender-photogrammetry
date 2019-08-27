import bpy
import os
import bmesh
from mathutils import Vector, Matrix

from ..utils import set_active_collection, get_image_size


def load(properties, data, *args, **kwargs):
    """ Imports photogrammetry data into the current scene.
    """
    scene = kwargs.get('scene', None)
    if not scene:
        raise Exception('Scene required to load data in blender.load')
    collection = set_active_collection(**kwargs)
    camera_collection = set_active_collection(name='Cameras', parent=collection, **kwargs)

    resolution = data.get('resolution', None)
    if not resolution and len(data['cameras']):
        resolution = get_image_size(next(c for c in data['cameras'].values())['filename'])
    if properties.update_render_size:
        scene.render.resolution_x, scene.render.resolution_y = resolution

    if properties.animate_camera:
        name = 'AnimatedPhotogrammetryCamera'
        cdata = bpy.data.cameras.new(name)
        cdata.sensor_width = 35
        animated_camera = bpy.data.objects.new(name, cdata)
        camera_collection.objects.link(animated_camera)

    ordered_cameras = sorted(data['cameras'].values(), key=lambda c: os.path.basename(c['filename']))
    for i, camera in enumerate(ordered_cameras):
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
        camera_collection.objects.link(cam)

        # add background images per camera!
        cdata.show_background_images = True
        bg = cdata.background_images.new()
        image_path = camera['filename']
        if properties.relative_paths:
            image_path = bpy.path.relpath(image_path)
        img = bpy.data.images.load(image_path, check_existing=True)
        bg.image = img
        bg.alpha = properties.camera_alpha
        bg.display_depth = properties.camera_display_depth

        # set parameters
        cam.location = translation
        cam.rotation_euler = rotation
        cdata.sensor_width = 35
        cdata.lens = (camera['f'] * 35) / scene.render.resolution_x
        if 'principal' in camera:
            # https://blender.stackexchange.com/questions/58235/what-are-the-units-for-camera-shift
            x, y = resolution
            px, py = camera['principal']
            max_dimension = float(max(x, y))
            cdata.shift_x = (x / 2.0 - px) / max_dimension
            cdata.shift_y = (y / 2.0 - py) / max_dimension

        if animated_camera:
            animated_camera.location = cam.location
            animated_camera.rotation_euler = cam.rotation_euler
            animated_camera.keyframe_insert('location', frame=i+1)
            animated_camera.keyframe_insert('rotation_euler', frame=i+1)

            # only needs to occur for the first camera - animating these properties could be trippy
            if i == 0:
                animated_camera.data.lens = cdata.lens
                animated_camera.data.shift_x = cdata.shift_x
                animated_camera.data.shift_y = cdata.shift_y


    coords = []
    for tracker in data['trackers'].values():
        coords.append(Vector(tracker['co']))

    mesh = bpy.data.meshes.new("PhotogrammetryPoints")
    obj = bpy.data.objects.new("PhotogrammetryPoints", mesh)

    collection.objects.link(obj)
    scene.view_layers[0].objects.active = obj
    obj.select_set(True)

    # add all coords from bundler points as vertices
    bm = bmesh.new()
    for v in coords:
        bm.verts.new(v)

    # make the bmesh the object's mesh
    bm.to_mesh(mesh)  
    bm.free()

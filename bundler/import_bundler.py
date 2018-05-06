import bpy
import os
import bmesh
from mathutils import Vector, Matrix


def import_bundler(bundle_path, list_path, scene):
    """ Imports a scene in bundler format.
    :param bundle_path: the target bundle.out file
    :param list_path: the target list.txt file
    :param scene: the scene to import into
    """
    with open(list_path, 'r') as f:
        imagepath = f.readline().strip()
    img = bpy.data.images.load(os.path.join(os.path.dirname(list_path), imagepath))
    width, height = img.size
    scene.render.resolution_x = width
    scene.render.resolution_y = height

    with open(bundle_path, 'r') as f:
        lines = f.readlines()

    total_cameras, total_points = map(int, lines[1].split())
    for i in range(total_cameras):
        # each camera uses 5 lines
        idx = 2 + i * 5
        # read data
        focal, k1, k2 = list(map(float, lines[idx].split()))
        rotation = []
        rotation.append(map(float, lines[idx + 1].split()))
        rotation.append(map(float, lines[idx + 2].split()))
        rotation.append(map(float, lines[idx + 3].split()))
        translation = Vector(map(float, lines[idx + 4].split()))
        
        # rotation in file needs to be transposed to work properly
        mrot = Matrix(list(map(list, rotation)))
        mrot.transpose()
        rotation = mrot.to_euler('XYZ')

        # https://github.com/simonfuhrmann/mve/wiki/Math-Cookbook
        # t = -R * c
        # where c is the real world position as I've calculated, and t is the camera location stored in bundle.out
        translation = -1 * mrot * translation
        
        # create and link camera
        name = "BundlerCamera{}".format(i)
        data = bpy.data.cameras.new(name)
        cam = bpy.data.objects.new(name, data)
        scene.objects.link(cam)

        # set parameters
        cam.location = translation
        cam.rotation_euler = rotation
        data.sensor_width = 35
        data.lens = (focal * 35) / scene.render.resolution_x

    coords = []
    for i in range(total_points):
        # each point uses 3 lines
        idx = 2 + total_cameras * 5 + i * 3
        coords.append(Vector(map(float, lines[idx].split())))
        # TODO: use rgb for vertex colours
        rgb = list(map(int, lines[idx + 1].split()))
        # ignore 2d view list

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

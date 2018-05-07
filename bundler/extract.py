import bpy
import os
import shutil
import subprocess
from mathutils import Vector, Matrix
from collections import namedtuple


def extract(properties, *args, **kargs):
    dirpath = bpy.path.abspath(properties.dirpath)
    print(dirpath)

    # # TODO: read list.txt to get image paths to detect image size
    # resolution_x = int(scene.render.resolution_x * (scene.render.resolution_percentage / 100))

    # with open(os.path.join(blend, 'bundle.rd.out'), 'r') as f:
    #     lines = f.readlines()

    # total_cameras, total_points = map(int, lines[1].split())
    # for i in range(int(total_cameras)):
    #     # each camera uses 5 lines
    #     idx = 2 + i * 5
    #     # read data
    #     focal, k1, k2 = list(map(float, lines[idx].split()))
    #     rotation = []
    #     rotation.append(map(float, lines[idx + 1].split()))
    #     rotation.append(map(float, lines[idx + 2].split()))
    #     rotation.append(map(float, lines[idx + 3].split()))
    #     mrot = Matrix(list(map(list, rotation)))
        
    #     # rotation in file needs to be transposed to work properly
    #     mrot.transpose()
    #     rotation = mrot.to_euler('XYZ')

    #     translation = Vector(map(float, lines[idx + 4].split()))
        
    #     # https://github.com/simonfuhrmann/mve/wiki/Math-Cookbook
    #     # t = -R * c
    #     # where c is the real world position as I've calculated, and t is the camera location stored in bundle.out
    #     translation = -1 * mrot * translation
        
    #     # create and link camera
    #     name = "Camera{}".format(i)
    #     data = bpy.data.cameras.new(name)
    #     cam = bpy.data.objects.new(name, data)
    #     scene.objects.link(cam)
    #     # set parameters
    #     cam.location = translation
    #     cam.rotation_euler = rotation
    #     #int(resolution_x * (cd.lens / cd.sensor_width))
    #     data.sensor_width = 35
    #     data.lens = (focal * 35) / resolution_x



    # coords = []
    # for i in range(int(total_points)):
    #     print(i)
    #     # each point uses 3 lines
    #     idx = 2 + int(total_cameras) * 5 + i * 3
    #     coords.append(Vector(map(float, lines[idx].split())))
    #     # rgb = list(map(int, lines[idx + 1].split())
    #     # ignore 2d view list
            
    # import bmesh

    # mesh = bpy.data.meshes.new("mesh")  # add a new mesh
    # obj = bpy.data.objects.new("MyObject", mesh)  # add a new object using the mesh

    # scene = bpy.context.scene
    # scene.objects.link(obj)  # put the object into the scene (link)
    # scene.objects.active = obj  # set as the active object in the scene
    # obj.select = True  # select object

    # mesh = bpy.context.object.data
    # bm = bmesh.new()

    # for v in coords:
    #     bm.verts.new(v)  # add a new vert

    # # make the bmesh the object's mesh
    # bm.to_mesh(mesh)  
    # bm.free()  # always do this when finished
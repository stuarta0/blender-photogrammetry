from bpy.props import StringProperty, BoolProperty, IntProperty, FloatProperty, PointerProperty
from bpy.types import PropertyGroup


class PHOTOGRAMMETRY_PG_input_colmap(PropertyGroup):
    dirpath: StringProperty(name='Workspace Directory', subtype='DIR_PATH', description='Directory containing the sparse reconstruction (cameras.bin, images.bin, points3D.bin)')
    
    def draw(self, layout):
        layout.prop(self, 'dirpath')


# class PHOTOGRAMMETRY_PG_colmap_patch_match_stereo(PropertyGroup):
#     gpu_index: StringProperty(name='GPU Index', default='-1', description='Comma-separated list of GPUs to run dense reconstruction. You can run multiple threads on the same GPU by specifying the same GPU index twice, e.g. "0,0,1,1,2,3"')
#     depth_min: IntProperty(name='Depth Min', default=-1)
#     depth_max: IntProperty(name='Depth Max', default=-1)
#     window_radius: IntProperty(name='Window Radius', default=5, min=1, description='For scenes with weakly textured surfaces it can help to increase maximum image size and have a large patch window radius')
#     window_step: IntProperty(name='Window Step', default=1, min=1, description='Speed up dense reconstruction by increasing the window step to 2')
#     filter_: BoolProperty(name='Filter', default=True)
#     filter_min_ncc: FloatProperty(name='Filter Min NCC', default=0.1, min=0, description='For scenes with weakly textured surfaces, it can help to reduce this filtering threshold for the photometric consistency cost')
#     cache_size: IntProperty(name='Cache Size', default=8, description='CPU memory in gigabytes')

#     def draw(self, layout):
#         layout.prop(self, 'gpu_index')
#         layout.prop(self, 'depth_min')
#         layout.prop(self, 'depth_max')
#         layout.prop(self, 'window_radius')
#         layout.prop(self, 'window_step')
#         layout.prop(self, 'filter_')
#         layout.prop(self, 'filter_min_ncc')
#         layout.prop(self, 'cache_size')


class PHOTOGRAMMETRY_PG_output_colmap(PropertyGroup):
    dirpath: StringProperty(name='Workspace Directory', subtype='DIR_PATH', default='//colmap')
    overwrite: BoolProperty(name='Overwrite Workspace Directory', default=True, description='If the workspace directory exists, all existing COLMAP files will be deleted. If you have already run dense reconstruction and only want to generate meshes, do not overwrite the workspace directory')
    max_image_size: IntProperty(name='Max Image Size', subtype='PIXEL', default=0, min=0, description='If you run out of GPU memory during reconstruction, you can reduce the maximum image size by setting this option (0px = no limit)')
    import_points: BoolProperty(name='Reconstruct point cloud', default=True, description='If false, just export COLMAP sparse model without reconstructing. If one of the mesh options are chosen, dense reconstruction will occur regardless')
    import_poisson: BoolProperty(name='Create poisson mesh', default=False, description='Run poisson_mesher on the dense reconstruction and import the resulting mesh')
    import_delaunay: BoolProperty(name='Create delaunay mesh', default=False, description='Run delaunay_mesher on the dense reconstruction and import the resulting mesh')
    import_openmvs: BoolProperty(name='Create openMVS textured mesh', default=False, description='Run openMVS on COLMAP dense reconstruction and import the resulting textured mesh')
    
    def draw(self, layout):
        layout.prop(self, 'dirpath')
        layout.prop(self, 'overwrite')
        layout.prop(self, 'max_image_size')
        layout.prop(self, 'import_points')
        layout.prop(self, 'import_poisson')
        layout.prop(self, 'import_delaunay')
        layout.prop(self, 'import_openmvs')

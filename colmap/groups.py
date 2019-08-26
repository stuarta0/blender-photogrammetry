from bpy.props import StringProperty, BoolProperty, IntProperty
from bpy.types import PropertyGroup


class PHOTOGRAMMETRY_PG_input_colmap(PropertyGroup):
    dirpath: StringProperty(name='Workspace Directory', subtype='DIR_PATH', description='Directory containing the sparse reconstruction (cameras.bin, images.bin, points3D.bin)')
    
    def draw(self, layout):
        layout.prop(self, 'dirpath')


class PHOTOGRAMMETRY_PG_output_colmap(PropertyGroup):
    dirpath: StringProperty(name='Workspace Directory', subtype='DIR_PATH', default='//colmap')
    max_image_size: IntProperty(name='Max Image Size', subtype='PIXEL', default=0, min=0, description='If you run out of GPU memory during reconstruction, you can reduce the maximum image size by setting this option (0px means no limit)')
    import_points: BoolProperty(name='Import point cloud after reconstruction', default=False)
    
    def draw(self, layout):
        layout.prop(self, 'dirpath')
        layout.prop(self, 'max_image_size')
        layout.prop(self, 'import_points')

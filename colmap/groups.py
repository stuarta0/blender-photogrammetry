from bpy.props import StringProperty, BoolProperty, IntProperty
from bpy.types import PropertyGroup


class COLMAPPropertyGroup(PropertyGroup):
    dirpath = StringProperty(name='Workspace Directory', subtype='DIR_PATH', default='//colmap')
    max_image_size = IntProperty(name='Max Image Size', default=-1, min=-1, description='If you run out of GPU memory during reconstruction, you can reduce the maximum image size by setting this option (-1 means no limit)')
    import_points = BoolProperty(name='Import point cloud after reconstruction', default=False)
    
    def draw(self, layout):
        layout.prop(self, 'dirpath')
        layout.prop(self, 'max_image_size')
        layout.prop(self, 'import_points')

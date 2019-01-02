from bpy.props import StringProperty, BoolProperty
from bpy.types import PropertyGroup


class COLMAPPropertyGroup(PropertyGroup):
    dirpath = StringProperty(name='Sparse Model Directory', subtype='DIR_PATH', default='//colmap')
    import_points = BoolProperty(name='Import point cloud after reconstruction', default=False)
    
    def draw(self, layout):
        layout.prop(self, 'dirpath')
        layout.prop(self, 'import_points')

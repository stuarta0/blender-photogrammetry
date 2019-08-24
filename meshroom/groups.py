from bpy.props import StringProperty, BoolProperty
from bpy.types import PropertyGroup

class PHOTOGRAMMETRY_PG_meshroom(PropertyGroup):
    filepath: StringProperty(name="Filepath", description="Filename of cameras.sfm file", subtype='FILE_PATH')

    def draw(self, layout):
        layout.prop(self, 'filepath')
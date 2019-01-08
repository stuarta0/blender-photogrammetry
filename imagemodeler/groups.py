from bpy.props import StringProperty, BoolProperty
from bpy.types import PropertyGroup

class ImageModelerPropertyGroup(PropertyGroup):
    filepath = StringProperty(name="Filepath", description="Filename of source ImageModeler file", subtype='FILE_PATH')
    imagepath = StringProperty(name="Image directory", subtype='DIR_PATH', description="Path to directory containg images referenced by ImageModeler file. Defaults to same directory as ImageModeler file")
    subdirs = BoolProperty(name='Search subdirectories for images', default=True)

    def draw(self, layout):
        layout.prop(self, 'filepath')
        layout.prop(self, 'imagepath')
        layout.prop(self, 'subdirs')

from bpy.props import StringProperty, BoolProperty
from bpy.types import PropertyGroup

class PHOTOGRAMMETRY_PG_input_visualsfm(PropertyGroup):
    filepath: StringProperty(name="Filepath", description="Filename of NVM file", subtype='FILE_PATH')
    imagepath: StringProperty(name="Image directory", subtype='DIR_PATH', description="Path to directory containg images referenced by NVM file. Defaults to same directory as NVM file")
    subdirs: BoolProperty(name='Search subdirectories for images', default=True)

    def draw(self, layout):
        layout.prop(self, 'filepath')
        layout.prop(self, 'imagepath')
        layout.prop(self, 'subdirs')


class PHOTOGRAMMETRY_PG_output_visualsfm(PropertyGroup):
    dirpath: StringProperty(name='Workspace Directory', subtype='DIR_PATH', default='//visualsfm')

    def draw(self, layout):
        layout.prop(self, 'dirpath')

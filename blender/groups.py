import os
import bpy
from bpy.props import StringProperty, IntProperty, BoolProperty
from bpy.types import PropertyGroup


class PHOTOGRAMMETRY_PG_input_blender(PropertyGroup):
    clip: StringProperty(name='Movie Clip')
    frame_step: IntProperty(name='Frame Step', description='Number of frames to skip when exporting', default=1)
    dirpath: StringProperty(name='Image Directory', subtype='DIR_PATH', default=os.path.join('//renderoutput', 'photogrammetry'))
    
    def draw(self, layout):
        layout.prop(self, 'dirpath')
        layout.prop_search(self, 'clip', bpy.data, 'movieclips')
        layout.prop(self, 'frame_step')

class PHOTOGRAMMETRY_PG_output_blender(PropertyGroup):
    update_render_size: BoolProperty(name='Update render size', description="Update the active scene's render size to the first image size", default=True)
    relative_paths: BoolProperty(name='Use relative paths for images', description='When adding background images for cameras, link images using relative paths', default=True)

    def draw(self, layout):
        layout.prop(self, 'update_render_size')
        layout.prop(self, 'relative_paths')

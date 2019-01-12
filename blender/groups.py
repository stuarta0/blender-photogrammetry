import os
import bpy
from bpy.props import StringProperty, IntProperty, BoolProperty, FloatProperty, EnumProperty
from bpy.types import PropertyGroup, Panel


class PHOTOGRAMMETRY_PG_input_blender(PropertyGroup):
    clip: StringProperty(name='Movie Clip')
    frame_step: IntProperty(name='Frame Step', description='Number of frames to skip when exporting', default=1, min=1)
    dirpath: StringProperty(name='Image Directory', subtype='DIR_PATH', default=os.path.join('//renderoutput', 'photogrammetry'))
    
    def draw(self, layout):
        layout.prop(self, 'dirpath')
        layout.prop_search(self, 'clip', bpy.data, 'movieclips')
        layout.prop(self, 'frame_step')

class PHOTOGRAMMETRY_PG_output_blender(PropertyGroup):
    update_render_size: BoolProperty(name='Update render size', description="Update the active scene's render size to the first image size", default=True)
    relative_paths: BoolProperty(name='Use relative paths for images', description='When adding background images for cameras, link images using relative paths', default=True)
    camera_alpha: FloatProperty(name='Camera Background Alpha', default=0.5, min=0, max=1)
    camera_display_depth: EnumProperty(items=[
        ('BACK', 'Back', 'Display image behind the 3D objects'),
        ('FRONT', 'Front', 'Display image in front of the 3D objects'),
    ], name='Camera Background Display', default='BACK')

    def draw(self, layout):
        layout.prop(self, 'update_render_size')
        layout.prop(self, 'relative_paths')
        layout.prop(self, 'camera_alpha')
        layout.prop(self, 'camera_display_depth', expand=True)

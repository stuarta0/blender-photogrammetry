import bpy
from bpy.props import StringProperty, IntProperty
from bpy.types import PropertyGroup


class Input_BlenderPropertyGroup(PropertyGroup):
    clip = StringProperty(name='Movie Clip')
    frame_step = IntProperty(name='Frame Step', description='Number of frames to skip when exporting', default=1)
    
    def draw(self, layout):
        layout.prop_search(self, 'clip', bpy.data, 'movieclips')
        layout.prop(self, 'frame_step')

from bpy.props import StringProperty
from bpy.types import PropertyGroup


class PHOTOGRAMMETRY_PG_bundler(PropertyGroup):
    dirpath = StringProperty(name='Bundler Data Directory', subtype='DIR_PATH', default='//bundler')
    
    def draw(self, layout):
        layout.prop(self, 'dirpath')

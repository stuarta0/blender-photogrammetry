from bpy.props import StringProperty
from bpy.types import PropertyGroup


class BundlerPropertyGroup(PropertyGroup):
    dirpath: StringProperty(name='Bundler Data Directory', subtype='DIR_PATH', default='//bundler')
    
    def draw(self, layout):
        layout.prop(self, 'dirpath')

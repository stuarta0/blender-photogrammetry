bl_info = {
    "name": "Dense Reconstruction",
    "author": "Stuart Attenborrow",
    "version": (1, 0, 0),
    "blender": (2, 80, 0),
    "location": "Properties > Scene",
    "description": "Provides the ability to process data in various photogrammetry tools, including blender's motion tracking output",
    "wiki_url": "https://www.github.com/stuarta0/blender-photogrammetry",
    "category": "Photogrammetry",
}

import platform
import os

import bpy
from bpy.props import PointerProperty, IntProperty, FloatProperty, StringProperty, EnumProperty, BoolProperty
from bpy.types import AddonPreferences, PropertyGroup, Operator
from bpy_extras.io_utils import ExportHelper, ImportHelper

from .blender.groups import PHOTOGRAMMETRY_PG_input_blender, PHOTOGRAMMETRY_PG_output_blender
from .blender.extract import extract as extract_blender
from .blender.load import load as load_blender

from .bundler.groups import PHOTOGRAMMETRY_PG_bundler
from .bundler.extract import extract as extract_bundler
from .bundler.load import load as load_bundler

from .imagemodeler.groups import PHOTOGRAMMETRY_PG_image_modeller
from .imagemodeler.extract import extract as extract_imagemodeler

from .pmvs.groups import PHOTOGRAMMETRY_PG_pmvs
from .pmvs.load import load as load_pmvs

from .colmap.groups import PHOTOGRAMMETRY_PG_colmap
from .colmap.load import load as load_colmap


class PhotogrammetryPreferences(AddonPreferences):
    bl_idname = __name__
    platform: StringProperty(
        name='Platform',
        description='Path to the binaries for this platform in the format {os}',
        default=platform.system().lower()
    )
    
    def draw(self, context):
        layout = self.layout
        layout.prop(self, "platform")
        layout.label(text="Valid platforms are 'linux' or 'windows'.")


class PHOTOGRAMMETRY_OT_process(bpy.types.Operator):
    bl_idname = "photogrammetry.process"
    bl_label = "Process photogrammetry from current scene settings"

    def execute(self, context):
        scene = context.scene
        p = scene.photogrammetry
        
        print('process photogrammetry')
        print(p.input)
        print(p.output)
        extract_props = getattr(p, p.input, None)
        load_props = getattr(p, p.output, None)

        from pprint import pprint
        data = None
        if p.input == 'in_blender':
            data = extract_blender(extract_props, scene=scene)
        elif p.input == 'in_bundler':
            data = extract_bundler(extract_props)
        elif p.input == 'in_rzi':
            data = extract_imagemodeler(extract_props)
        
        pprint(data)

        if data:
            if p.output == 'out_blender':
                load_blender(load_props, data, scene=scene)
            if p.output == 'out_bundler':
                load_bundler(load_props, data, scene=scene)
            if p.output == 'out_pmvs':
                load_pmvs(load_props, data, scene=scene)
            if p.output == 'out_colmap':
                load_colmap(load_props, data, scene=scene)

        return{'FINISHED'}    


# To change over to a dynamic I/O architecture (where formats can be added/removed as needed), see here:
# https://hamaluik.com/posts/dynamic-blender-properties/
class PHOTOGRAMMETRY_PG_master(PropertyGroup):
    input: EnumProperty(name='From', items=(
                            ('in_blender', 'Blender Motion Tracking', 'Use tracking data from current scene'),
                            ('in_bundler', 'Bundler', 'Read a Bundler OUT file'),
                            ('in_rzi', 'ImageModeler', 'Read an ImageModeler RZI file'),
                        ), default='in_blender')
    in_blender: PointerProperty(type=PHOTOGRAMMETRY_PG_input_blender)
    in_bundler: PointerProperty(type=PHOTOGRAMMETRY_PG_bundler)
    in_rzi: PointerProperty(type=PHOTOGRAMMETRY_PG_image_modeller)
                        
    output: EnumProperty(name='To', items=(
                             ('out_blender', 'Blender', 'Import data into current scene'),
                             ('out_bundler', 'Bundler', 'Output images and bundle.out'),
                             ('out_pmvs', 'PMVS', 'Use PMVS2 to generate a dense point cloud'),
                             ('out_colmap', 'COLMAP', 'Use COLMAP to generate a dense point cloud and reconstructed mesh'),
                         ), default='out_pmvs')
    out_blender: PointerProperty(type=PHOTOGRAMMETRY_PG_output_blender)
    out_bundler: PointerProperty(type=PHOTOGRAMMETRY_PG_bundler)
    out_pmvs: PointerProperty(type=PHOTOGRAMMETRY_PG_pmvs)
    out_colmap: PointerProperty(type=PHOTOGRAMMETRY_PG_colmap)
    
    def draw(self, layout):
        layout.use_property_split = True # Active single-column layout
        layout.prop(self, 'input')
        try:
            getattr(self, self.input).draw(layout)
        except AttributeError:
            layout.label(text='No options')
        
        layout.separator()
        layout.prop(self, 'output')
        try:
            getattr(self, self.output).draw(layout)
        except AttributeError:
            layout.label(text='No options')
            
        layout.separator()
        layout.operator("photogrammetry.process", text='Process')


class PHOTOGRAMMETRY_PT_settings(bpy.types.Panel):
    bl_label = "Photogrammetry Tools"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "scene"
    
    def draw(self, context):
        layout = self.layout
        p = context.scene.photogrammetry
        p.draw(layout)


classes = (
    PHOTOGRAMMETRY_PG_input_blender,
    PHOTOGRAMMETRY_PG_output_blender,
    PHOTOGRAMMETRY_PG_bundler,
    PHOTOGRAMMETRY_PG_pmvs,
    PHOTOGRAMMETRY_PG_colmap,
    PHOTOGRAMMETRY_PG_image_modeller,
    PHOTOGRAMMETRY_PG_master,
    PHOTOGRAMMETRY_PT_settings,
    PHOTOGRAMMETRY_OT_process,
    PhotogrammetryPreferences,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.photogrammetry = PointerProperty(type=PHOTOGRAMMETRY_PG_master)
    
    print('[blender-photogrammetry] Platform:', platform.system().lower())
    if platform.system().lower() == 'linux':
        script_file = os.path.realpath(__file__)
        addon_dir = os.path.dirname(script_file)
        print('[blender-photogrammetry] Attempting to set execute flag on precompiled binaries in:')
        print(addon_dir)
        
        targets = ['pmvs', 'RadialUndistort', 'Bundle2PMVS']
        try:
            for root, dirs, files in os.walk(addon_dir):
                for f in files:
                    if any([f.startswith(t) for t in targets]):
                        os.chmod(os.path.join(root, f), 0o755)
        except Exception as ex:
            print('Unable to set precompiled binaries execute flag.')
            print(ex)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.photogrammetry


if __name__ == "__main__":
    register()

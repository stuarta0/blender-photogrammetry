bl_info = {
    "name": "Dense Photogrammetry Reconstruction",
    "author": "Stuart Attenborrow",
    "version": (1, 2, 0),
    "blender": (2, 80, 0),
    "location": "Properties > Scene",
    "description": "Provides the ability to generate dense point clouds using various photogrammetry tools, from inputs including Blender's motion tracking output",
    "wiki_url": "https://www.github.com/stuarta0/blender-photogrammetry",
    "category": "Photogrammetry",
}

import platform
import os
from importlib import import_module
from typing import Dict, List

import bpy
from bpy.props import PointerProperty, IntProperty, FloatProperty, StringProperty, EnumProperty, BoolProperty
from bpy.types import AddonPreferences, PropertyGroup, Operator
from bpy_extras.io_utils import ExportHelper, ImportHelper

from .utils import PhotogrammetryModule, get_binpath_for_module, get_binary_path, CroppingPrettyPrinter


# modules will exist as directories in the current directory
# if they're not a python module they'll fail to import and we'll skip them
modules = [name for name in os.listdir(os.path.dirname(__file__)) if os.path.isdir(os.path.join(os.path.dirname(__file__), name))]

inputs: Dict[str, PhotogrammetryModule] = {}
outputs: Dict[str, PhotogrammetryModule] = {}
binaries: List[str] = []

for m in modules:
    try:
        currentModule = import_module(f'.{m}', __name__)
        importer = getattr(currentModule, 'importer', None)
        exporter = getattr(currentModule, 'exporter', None)
        binaryNames = getattr(currentModule, 'binaries', [])
        if not (importer or exporter):
            raise AttributeError('Attributes "importer" and/or "exporter" must be defined in module')
    except Exception as ex:
        print(f'Problem importing photogrammetry module "{m}": {ex}')
        continue

    currentBinaries = [get_binary_path(get_binpath_for_module(m), name) for name in binaryNames]
    if any([not binpath for binpath in currentBinaries]):
        print(f'Photogrammetry module "{m}" specified binaries that could not be found {currentModule.binaries}')
        continue
    for binpath in currentBinaries:
        binaries.append(binpath)

    if importer:
        inputs.setdefault(f'in_{m}', importer)
    if exporter:
        outputs.setdefault(f'out_{m}', exporter)


class PHOTOGRAMMETRY_PT_preferences(AddonPreferences):
    bl_idname = __name__
    collection_name: StringProperty(
        name='Collection Name',
        description='Name of the collection that will be created when adding photogrammetry objects',
        default='Photogrammetry'
    )
    
    def draw(self, context):
        layout = self.layout
        layout.prop(self, "collection_name")


class PHOTOGRAMMETRY_OT_process(bpy.types.Operator):
    bl_idname = "photogrammetry.process"
    bl_label = "Process photogrammetry from current scene settings"

    def execute(self, context):
        scene = context.scene
        p = scene.photogrammetry
        p.last_error = ''
        
        print('process photogrammetry')
        print(p.input)
        print(p.output)

        if not (p.input in inputs and p.output in outputs):
            return {'FINISHED'}

        extract_props = getattr(p, p.input, None)
        load_props = getattr(p, p.output, None)

        try:
            data = inputs[p.input].func(extract_props, scene=scene)
        except AttributeError as ex:
            p.last_error = str(ex)
            return {'FINISHED'}
        
        pprint = CroppingPrettyPrinter(maxlist=10, maxdict=10)
        pprint.pprint(data)
        if data:
            try:
                outputs[p.output].func(load_props, data, scene=scene)
            except AttributeError as ex:
                p.last_error = str(ex)
                return {'FINISHED'}

        return {'FINISHED'}


# # The following class is generated dynamically based on which modules are present with valid binaries
# # Concept derived from: https://blog.hamaluik.ca/posts/dynamic-blender-properties/
# class PHOTOGRAMMETRY_PG_master(PropertyGroup):
#     input: EnumProperty(name='From', items=(
#                             ('in_blender', 'Blender Motion Tracking', 'Use tracking data from current scene'),
#                             ('in_bundler', 'Bundler', 'Read a Bundler OUT file'),
#                             ('in_rzi', 'ImageModeler', 'Read an ImageModeler RZI file'),
#                         ), default='in_blender')
#     in_blender: PointerProperty(type=PHOTOGRAMMETRY_PG_input_blender)
#     in_bundler: PointerProperty(type=PHOTOGRAMMETRY_PG_bundler)
#     in_rzi: PointerProperty(type=PHOTOGRAMMETRY_PG_image_modeller)
                        
#     output: EnumProperty(name='To', items=(
#                              ('out_blender', 'Blender', 'Import data into current scene'),
#                              ('out_bundler', 'Bundler', 'Output images and bundle.out'),
#                              ('out_pmvs', 'PMVS', 'Use PMVS2 to generate a dense point cloud'),
#                              ('out_colmap', 'COLMAP', 'Use COLMAP to generate a dense point cloud and reconstructed mesh'),
#                          ), default='out_pmvs')
#     out_blender: PointerProperty(type=PHOTOGRAMMETRY_PG_output_blender)
#     out_bundler: PointerProperty(type=PHOTOGRAMMETRY_PG_bundler)
#     out_pmvs: PointerProperty(type=PHOTOGRAMMETRY_PG_pmvs)
#     out_colmap: PointerProperty(type=PHOTOGRAMMETRY_PG_colmap)

def draw_master(self, layout):
    # self = PHOTOGRAMMETRY_PG_master instance
    # layout = bpy.data.screens['Layout']...UILayout
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

    if self.last_error:
        layout.separator()
        box = layout.box()
        # waiting for https://developer.blender.org/D7496
        for line in self.last_error.split('\n'):
            box.label(text=line)


def on_input_updated(self, context):
    self.last_error = ''

def on_output_updated(self, context):
    self.last_error = ''

attributes = {
    "input": EnumProperty(name='From', items=tuple(
        (key, importer.name, importer.description) for key, importer in inputs.items()
    ), update=on_input_updated),
    "output": EnumProperty(name='To', items=tuple(
        (key, exporter.name, exporter.description) for key, exporter in outputs.items()
    ), update=on_output_updated),
    "last_error": StringProperty(name='Error')
}
for key, importer in inputs.items():
    if importer.property_group:
        attributes.setdefault(key, PointerProperty(type=importer.property_group))
for key, exporter in outputs.items():
    if exporter.property_group:
        attributes.setdefault(key, PointerProperty(type=exporter.property_group))

PHOTOGRAMMETRY_PG_master = type(
    "PHOTOGRAMMETRY_PG_master",
    (PropertyGroup,),
    {
        '__annotations__': attributes,
        'draw': draw_master,
    },
)


class PHOTOGRAMMETRY_PT_settings(bpy.types.Panel):
    bl_label = "Photogrammetry Tools"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "scene"
    
    def draw(self, context):
        layout = self.layout
        p = context.scene.photogrammetry
        p.draw(layout)


classes = list(set([i.property_group for i in inputs.values() if i.property_group] + [o.property_group for o in outputs.values() if o.property_group]))
classes = classes + [
    PHOTOGRAMMETRY_PT_preferences,
    PHOTOGRAMMETRY_PG_master,
    PHOTOGRAMMETRY_PT_settings,
    PHOTOGRAMMETRY_OT_process,
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.photogrammetry = PointerProperty(type=PHOTOGRAMMETRY_PG_master)
    
    print('[blender-photogrammetry] Platform:', platform.system().lower())
    if platform.system().lower() == 'linux':
        from pprint import pprint
        print('[blender-photogrammetry] Attempting to set execute flag on precompiled binaries:')
        pprint(binaries)
        
        try:
            for binpath in binaries:
                os.chmod(binpath, 0o755)
        except Exception as ex:
            print('Unable to set precompiled binaries execute flag.')
            print(ex)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.photogrammetry


if __name__ == "__main__":
    register()

bl_info = {
    "name": "Photogrammetry Processing",
    "author": "Stuart Attenborrow",
    "version": (0, 0, 1),
    "blender": (2, 79, 0),
    "location": "Properties > Scene",
    "description": "Provides the ability to process data in various photogrammetry tools, including blender's camera tracker output",
    "wiki_url": "https://www.github.com/stuarta0/blender-photogrammetry",
    "category": "Motion Tracking",
}

import platform
import os

import bpy
from bpy.props import PointerProperty, IntProperty, FloatProperty, StringProperty, EnumProperty
from bpy.types import AddonPreferences, PropertyGroup
from bpy_extras.io_utils import ExportHelper, ImportHelper

#from .export_colmap import export_colmap
#from .utils import run_colmap


class PhotogrammetryPreferences(AddonPreferences):
    bl_idname = __name__
    platform = StringProperty(
        name='Platform',
        description='Path to the binaries for this platform in the format {os}{bitness}',
        default=platform.system().lower()
    )
    
    def draw(self, context):
        layout = self.layout
        layout.prop(self, "platform")
        layout.label(text="Valid platforms are linux32, linux64, windows32 and windows64.")


# https://hamaluik.com/posts/dynamic-blender-properties/
class PMVSPropertyGroup(PropertyGroup):
    level = IntProperty(name='Level', default=1, min=0, description='When level is 0, original (full) resolution images are used. When level is 1, images are halved (or 4 times less pixels). And so on')
    csize = IntProperty(name='Cell Size', default=2, min=1, description='Controls the density of reconstructions. increasing the value of cell size leads to sparser reconstructions')
    threshold = FloatProperty(name='Threshold', default=0.7, min=0.15, description='A patch reconstruction is accepted as a success and kept, if its associcated photometric consistency measure is above this threshold. The software repeats three iterations of the reconstruction pipeline, and this threshold is relaxed (decreased) by 0.05 at the end of each iteration')
    wsize = IntProperty(name='Window Size', default=7, min=1, description='The software samples wsize x wsize pixel colors from each image to compute photometric consistency score.  Increasing the value leads to more stable reconstructions, but the program becomes slower')
    minImageNum = IntProperty(name='Min Image Num', default=3, min=2, description='Each 3D point must be visible in at least this many images to be reconstructed. If images are poor quality, increase this value')
    
    def draw(self, layout):
        layout.prop(self, 'level')
        layout.prop(self, 'csize')
        layout.prop(self, 'threshold')
        layout.prop(self, 'wsize')
        layout.prop(self, 'minImageNum')


class BundlerPropertyGroup(PropertyGroup):
    filename = StringProperty(name='Bundle .out file')
    
    def draw(self, layout):
        layout.prop(self, 'filename')


class BlenderPropertyGroup(PropertyGroup):
    clip = StringProperty(name='Movie Clip')
    frame_step = IntProperty(name='Frame Step', description='Number of frames to skip when exporting', default=1)
    
    def draw(self, layout):
        layout.prop_search(self, 'clip', bpy.data, 'movieclips')
        layout.prop(self, 'frame_step')


class PhotogrammetryPropertyGroup(PropertyGroup):
    input = EnumProperty(name='From', items=(
                            ('in_blender', 'Blender', 'Use camera tracking data from current scene'),
                            ('in_bundler', 'Bundler', 'Read a Bundler OUT file'),
                            ('in_rzi', 'ImageModeler', 'Read an ImageModeler RZI file'),
                        ), default='in_blender')
    in_blender = PointerProperty(type=BlenderPropertyGroup)
    in_bundler = PointerProperty(type=BundlerPropertyGroup)
                        
    output = EnumProperty(name='To', items=(
                             ('out_blender', 'Blender', 'Import data into current scene'),
                             ('out_bundler', 'Bundler', 'Output images and bundle.out'),
                             ('out_pmvs', 'PMVS', 'Use PMVS2 to generate a dense point cloud'),
                             ('out_colmap', 'COLMAP', 'Use COLMAP to generate a dense point cloud and mesh'),
                         ), default='out_pmvs')
    out_bundler = PointerProperty(type=BundlerPropertyGroup)
    out_pmvs = PointerProperty(type=PMVSPropertyGroup)
    
    def draw(self, layout):
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
        # layout.operator("photogrammetry.process")

class PhotogrammetryPanel(bpy.types.Panel):
    bl_idname = "export.photogrammetry"
    bl_label = "Photogrammetry Tools"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "scene"
    
    def draw(self, context):
        layout = self.layout
        p = context.scene.photogrammetry
        p.draw(layout)


classes = (
    BlenderPropertyGroup,
    BundlerPropertyGroup,
    PMVSPropertyGroup,
    PhotogrammetryPropertyGroup,
    PhotogrammetryPanel,
)
 

# def execute(self, context):
#     # with ProgressReport(context.window_manager) as progress:
#     if self.clip not in bpy.data.movieclips:
#         self.report({'ERROR'}, 'No movie clip selected')
#         return {'CANCELLED'}

#     scene = context.scene
#     clip = bpy.data.movieclips[self.clip]
#     export_colmap(scene, clip, self.filepath, range(scene.frame_start, scene.frame_end + 1, self.frame_step))
    
#     if self.exec_colmap:
#         user_prefs = context.user_preferences
#         addon_prefs = user_prefs.addons[__name__].preferences

#         script_file = os.path.realpath(__file__)
#         addon_dir = os.path.dirname(script_file)
        
#         bin_path = os.path.join(addon_dir, addon_prefs.platform)
#         if os.path.exists(bin_path):
#             run_colmap(bin_path, self.filepath)

#     return {'FINISHED'}

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.photogrammetry = PointerProperty(type=PhotogrammetryPropertyGroup)
    
    print('[blender-photogrammetry] Platform:', platform.system().lower())
    if platform.system().lower() == 'linux':
        script_file = os.path.realpath(__file__)
        addon_dir = os.path.dirname(script_file)
        print('[blender-photogrammetry] Attempting to set execute flag on precompiled binaries in:')
        print(addon_dir)
        # def set_execute(dirname):
        #     for f in os.listdir(dirname):
        #         os.chmod(os.path.join(dirname, f), 0o755)
        # try:
        #     for dirname in ['linux32', 'linux64']:
        #         set_execute(os.path.join(addon_dir, dirname))
        # except Exception as ex:
        #     print('Unable to set precompiled binaries execute flag.')
        #     print(ex)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.photogrammetry


if __name__ == "__main__":
    register()

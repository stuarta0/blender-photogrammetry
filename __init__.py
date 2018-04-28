bl_info = {
    "name": "Bundler OUT format",
    "author": "Stuart Attenborrow",
    "version": (0, 0, 1),
    "blender": (2, 79, 0),
    "location": "File > Import-Export",
    "description": "Import-Export Bundler OUT format (and associated files) for dense reconstruction using photogrammetry tools",
    "wiki_url": "https://www.github.com/stuarta0/blender-photogrammetry",
    "category": "Import-Export",
}

import platform
import bpy
import os
from bpy.types import AddonPreferences
from bpy_extras.io_utils import ExportHelper, ImportHelper

from .import_bundler import import_bundler
from .export_bundler import export_bundler
from .utils import bundle2pmvs, pmvs


def get_precompiled_bin_path():
    # https://stackoverflow.com/a/45125525
    arch = platform.machine().lower()
    if arch in ['x86_64', 'amd64', ]:
        arch = '64'
    else:
        arch = '32'

    os = platform.system().lower()
    return '{os}{arch}'.format(os=os, arch=arch)


class BlundlePreferences(AddonPreferences):
    bl_idname = __name__
    platform = bpy.props.StringProperty(
        name='Platform',
        description='Path to the binaries for this platform in the format {os}_{arch}',
        default=get_precompiled_bin_path()
    )

    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)
    #     print('Platform:', platform.system().lower())
    #     if platform.system().lower() == 'linux':
    #         script_file = os.path.realpath(__file__)
    #         addon_dir = os.path.dirname(script_file)
    #         print('Attempting to set execute flag on precompiled binaries in:')
    #         print(addon_dir)
    #         try:
    #             for exe in os.listdir(os.path.join(addon_dir, 'linux_386')) + os.listdir(os.path.join(addon_dir, 'linux_amd64')):
    #                 os.chmod(exe, 0o755)
    #         except Exception as ex:
    #             self.report({'INFO'}, 'Unable to set precompiled binaries execute flag.')
    
    def draw(self, context):
        layout = self.layout
        layout.prop(self, "platform")
        layout.label(text="Valid platforms are linux32, windows32 and windows64. linux64 can be used for 'Convert to PMVS' but not 'Execute PMVS'.")


class ImportBundler(bpy.types.Operator, ImportHelper):
    """Import a Bundler bundle.out file"""
    bl_idname = "import.bundler"
    bl_label = "Bundler (.out)"
    
    filename_ext = '.out'
    filter_glob = bpy.props.StringProperty(default='*.out', options={'HIDDEN'})

    def execute(self, context):
        bundle_path = self.filepath
        list_path = os.path.join(os.path.dirname(self.filepath), 'list.txt')

        if not (os.path.exists(bundle_path) and os.path.exists(list_path)):
            self.report({'ERROR'}, 'The bundler .out file must exist with an associated list.txt in the same directory')
            return {'CANCELLED'}

        import_bundler(bundle_path, list_path, context.scene)
        return {'FINISHED'}
    

def clip_updated(self, context):
    if self.clip in bpy.data.movieclips:
        clip = bpy.data.movieclips[self.clip]
        self['clip_size'] = '{x}x{y}'.format(x=clip.size[0], y=clip.size[1],)
        self['frame_step'] = max(1, int(context.scene.render.fps / 3))  # don't want too many frames when generating dense point clouds
    else:
        self['clip_size'] = ''


class ExportMovieClipBundler(bpy.types.Operator, ExportHelper):
    """Export a movie clip's tracking data to bundler *.out format"""
    bl_idname = "export.bundler"
    bl_label = "Bundler (.out)"
    
    filename_ext = '.out'
    filter_glob = bpy.props.StringProperty(default='*.out', options={'HIDDEN'})
    clip = bpy.props.StringProperty(name='Movie Clip', update=clip_updated)
    frame_step = bpy.props.IntProperty(name='Frame Step', description='Number of frames to skip when exporting frames for Bundler', default=1)
    clip_size = bpy.props.StringProperty(name='Size', default='')
    convert_pmvs = bpy.props.BoolProperty(name='Convert to PMVS', description='Convert bundle.out to PMVS format in subdirectory "pmvs"', default=False)
    exec_pmvs = bpy.props.BoolProperty(name='Execute PMVS', description='Run PMVS with default settings for dense reconstruction', default=False)


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.filepath = 'bundle'
        self.clip = bpy.context.scene.active_clip.name if bpy.context.scene.active_clip else ''
    
    
    def draw(self, context):
        # if not self.clip and context.scene.active_clip:
        #    self['clip'] = context.scene.active_clip.name
        
        layout = self.layout
        row = layout.row(align=True)
        row.prop_search(self, 'clip', bpy.data, 'movieclips')
        
        if self.clip_size:
            row = layout.row(align=True)
            row.label(text='')
            row.label(text=self.clip_size)
        
        row = layout.row(align=True)
        row.prop(self, 'frame_step')
        
        row = layout.row(align=True)
        row.prop(self, 'convert_pmvs')
        
        row = layout.row(align=True)
        row.prop(self, 'exec_pmvs')


    def execute(self, context):
        # with ProgressReport(context.window_manager) as progress:
        if self.clip not in bpy.data.movieclips:
            self.report({'ERROR'}, 'No movie clip selected')
            return {'CANCELLED'}

        scene = context.scene
        clip = bpy.data.movieclips[self.clip]
        export_bundler(scene, clip, self.filepath, range(scene.frame_start, scene.frame_end + 1, self.frame_step))
        
        if self.convert_pmvs or self.exec_pmvs:
            user_prefs = context.user_preferences
            addon_prefs = user_prefs.addons[__name__].preferences

            script_file = os.path.realpath(__file__)
            addon_dir = os.path.dirname(script_file)
            
            bin_path = os.path.join(addon_dir, addon_prefs.platform)
            pmvs_path = os.path.join(os.path.dirname(self.filepath), 'pmvs')
            if os.path.exists(bin_path):
                bundle2pmvs(bin_path, self.filepath, pmvs_path)
            
            if self.exec_pmvs:
                pmvs(bin_path, pmvs_path)

        return {'FINISHED'}


def menu_func_import(self, context):
    self.layout.operator(ImportBundler.bl_idname)


def menu_func_export(self, context):
    self.layout.operator(ExportMovieClipBundler.bl_idname)


classes = (
    ImportBundler,
    ExportMovieClipBundler,
    BlundlePreferences,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.INFO_MT_file_import.append(menu_func_import)
    bpy.types.INFO_MT_file_export.append(menu_func_export)
    
    
def unregister():
    bpy.types.INFO_MT_file_import.remove(menu_func_import)
    bpy.types.INFO_MT_file_export.remove(menu_func_export)
    
    for cls in classes:
        bpy.utils.unregister_class(cls)
    
    
if __name__ == "__main__":
    register()
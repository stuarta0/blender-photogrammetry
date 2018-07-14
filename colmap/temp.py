# bl_info = {
#     "name": "COLMAP format",
#     "author": "Stuart Attenborrow",
#     "version": (0, 0, 1),
#     "blender": (2, 79, 0),
#     "location": "File > Import-Export",
#     "description": "Import-Export COLMAP format from camera tracking data for dense reconstruction",
#     "wiki_url": "https://www.github.com/stuarta0/blender-photogrammetry",
#     "category": "Import-Export",
# }

# import platform
# import bpy
# import os
# from bpy.props import (StringProperty,
#                        BoolProperty,
#                        IntProperty,
#                        FloatProperty,
#                        EnumProperty,)
# from bpy.types import AddonPreferences
# from bpy_extras.io_utils import ExportHelper, ImportHelper

# from .export_colmap import export_colmap
# from .utils import run_colmap


# def get_precompiled_bin_path():
#     # https://stackoverflow.com/a/45125525
#     arch = platform.machine().lower()
#     if arch in ['x86_64', 'amd64', ]:
#         arch = '64'
#     else:
#         arch = '32'

#     os = platform.system().lower()
#     return '{os}{arch}'.format(os=os, arch=arch)


# class COLMAPPreferences(AddonPreferences):
#     bl_idname = __name__
#     platform = StringProperty(
#         name='Platform',
#         description='Path to the binaries for this platform in the format {os}{bitness}',
#         default=get_precompiled_bin_path()
#     )
    
#     def draw(self, context):
#         layout = self.layout
#         layout.prop(self, "platform")
#         layout.label(text="Valid platforms are linux32, linux64, windows32 and windows64.")


# # class ImportBundler(bpy.types.Operator, ImportHelper):
# #     """Import a Bundler bundle.out file"""
# #     bl_idname = "import.bundler"
# #     bl_label = "Bundler (.out)"
    
# #     filename_ext = '.out'
# #     filter_glob = StringProperty(default='*.out', options={'HIDDEN'})

# #     def execute(self, context):
# #         bundle_path = self.filepath
# #         list_path = listpath_from_bundle(bundle_path)

# #         if not (os.path.exists(bundle_path) and os.path.exists(list_path)):
# #             self.report({'ERROR'}, 'The bundler .out file must exist with an associated list.txt in the same directory')
# #             return {'CANCELLED'}

# #         import_bundler(bundle_path, list_path, context.scene)
# #         return {'FINISHED'}
    

# def clip_updated(self, context):
#     if self.clip in bpy.data.movieclips:
#         clip = bpy.data.movieclips[self.clip]
#         self['clip_size'] = '{x}x{y}'.format(x=clip.size[0], y=clip.size[1],)
#         self['frame_step'] = max(1, int(context.scene.render.fps / 3))  # don't want too many frames when generating dense point clouds
#     else:
#         self['clip_size'] = ''



# class ExportMovieClipCOLMAP(bpy.types.Operator, ExportHelper):
#     """Export a movie clip's tracking data to COLMAP format"""
#     bl_idname = "export.colmap"
#     bl_label = "COLMAP (.db)"
    
#     filename_ext = '.db'
#     filter_glob = StringProperty(default='*.out', options={'HIDDEN'})
#     clip = StringProperty(name='Movie Clip', update=clip_updated)
#     frame_step = IntProperty(name='Frame Step', description='Number of frames to skip when exporting frames for COLMAP', default=1)
#     clip_size = StringProperty(name='Size', default='')
#     exec_colmap = BoolProperty(name='Execute Reconstruction', description='Run COLMAP with default settings for dense reconstruction', default=False)

#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         self.filepath = 'database'
#         self.clip = bpy.context.scene.active_clip.name if bpy.context.scene.active_clip else ''
    
#     def draw(self, context):
#         # if not self.clip and context.scene.active_clip:
#         #    self['clip'] = context.scene.active_clip.name
        
#         layout = self.layout
#         row = layout.row(align=True)
#         row.prop_search(self, 'clip', bpy.data, 'movieclips')
        
#         if self.clip_size:
#             row = layout.row(align=True)
#             row.label(text='')
#             row.label(text=self.clip_size)
        
#         row = layout.row(align=True)
#         row.prop(self, 'frame_step')
        
#         row = layout.row(align=True)
#         row.prop(self, 'exec_colmap')

#     def execute(self, context):
#         # with ProgressReport(context.window_manager) as progress:
#         if self.clip not in bpy.data.movieclips:
#             self.report({'ERROR'}, 'No movie clip selected')
#             return {'CANCELLED'}

#         scene = context.scene
#         clip = bpy.data.movieclips[self.clip]
#         export_colmap(scene, clip, self.filepath, range(scene.frame_start, scene.frame_end + 1, self.frame_step))
        
#         if self.exec_colmap:
#             user_prefs = context.user_preferences
#             addon_prefs = user_prefs.addons[__name__].preferences

#             script_file = os.path.realpath(__file__)
#             addon_dir = os.path.dirname(script_file)
            
#             bin_path = os.path.join(addon_dir, addon_prefs.platform)
#             if os.path.exists(bin_path):
#                 run_colmap(bin_path, self.filepath)

#         return {'FINISHED'}


# def menu_func_import(self, context):
#     pass #self.layout.operator(ImportBundler.bl_idname)


# def menu_func_export(self, context):
#     self.layout.operator(ExportMovieClipCOLMAP.bl_idname)


# classes = (
#     #ImportBundler,
#     ExportMovieClipCOLMAP,
#     COLMAPPreferences,
#     #DebugSvg,
# )


# def register():
#     for cls in classes:
#         bpy.utils.register_class(cls)

#     bpy.types.INFO_MT_file_import.append(menu_func_import)
#     bpy.types.INFO_MT_file_export.append(menu_func_export)
    
#     print('[blender-photogrammetry] Platform:', platform.system().lower())
#     if platform.system().lower() == 'linux':
#         script_file = os.path.realpath(__file__)
#         addon_dir = os.path.dirname(script_file)
#         print('[blender-photogrammetry] Attempting to set execute flag on precompiled binaries in:')
#         print(addon_dir)

#         def set_execute(dirname):
#             for f in os.listdir(dirname):
#                 os.chmod(os.path.join(dirname, f), 0o755)

#         try:
#             for dirname in ['linux32', 'linux64']:
#                 set_execute(os.path.join(addon_dir, dirname))
#         except Exception as ex:
#             print('Unable to set precompiled binaries execute flag.')
#             print(ex)
    
    
# def unregister():
#     bpy.types.INFO_MT_file_import.remove(menu_func_import)
#     bpy.types.INFO_MT_file_export.remove(menu_func_export)
    
#     for cls in classes:
#         bpy.utils.unregister_class(cls)
    
    
# if __name__ == "__main__":
#     register()
bl_info = {
    "name": "Bundler OUT format",
    "author": "Stuart Attenborrow",
    "version": (0, 0, 1),
    "blender": (2, 79, 0),
    "location": "File > Import-Export",
    "description": "Import-Export Bundler OUT format and associated files for photogrammetry dense reconstruction",
    "wiki_url": "https://www.github.com/stuarta0/blundle",
    "category": "Import-Export",
}

import bpy
from bpy_extras.io_utils import ExportHelper

from .export import export

#from .export import export


def clip_updated(self, context):
    if self.clip in bpy.data.movieclips:
        clip = bpy.data.movieclips[self.clip]
        self['clip_size'] = '{x}x{y}'.format(x=clip.size[0], y=clip.size[1],)
        self['frame_step'] = int(context.scene.render.fps / 3)  # don't want too many frames when generating dense point clouds
    else:
        self['clip_size'] = ''


class ExportMovieClipBundler(bpy.types.Operator, ExportHelper):
    """Export a movie clip's tracking data to bundler *.out format"""
    bl_idname = "export.bundler"
    bl_label = "Bundler (.out)"
    
    filename_ext = '.out'
    filter_glob = bpy.props.StringProperty(default='bundle.out', options={'HIDDEN'})
    clip = bpy.props.StringProperty(name='Movie Clip', update=clip_updated)
    frame_step = bpy.props.IntProperty(name='Frame Step', description='Number of frames to skip when exporting frames for Bundler', default=1)
    clip_size = bpy.props.StringProperty(name='Size', default='')
    
    
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


    def execute(self, context):
        # with ProgressReport(context.window_manager) as progress:
        if self.clip not in bpy.data.movieclips:
            self.report({'ERROR'}, 'No movie clip selected')
            return {'CANCELLED'}
        
        scene = context.scene
        clip = bpy.data.movieclips[self.clip]
        export(scene, clip, self.filepath, range(scene.frame_start, scene.frame_end + 1, self.frame_step))
        return {'FINISHED'}


def menu_func(self, context):
    self.layout.operator(ExportMovieClipBundler.bl_idname)
    

def register():
    bpy.utils.register_class(ExportMovieClipBundler)
    bpy.types.INFO_MT_file_export.append(menu_func)
    
    
def unregister():
    bpy.types.INFO_MT_file_export.remove(menu_func)
    bpy.utils.unregister_class(ExportMovieClipBundler)
    
    
if __name__ == "__main__":
    register()
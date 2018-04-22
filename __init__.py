bl_info = {
    "name": "Bundler OUT format",
    "author": "Stuart Attenborrow",
    "version": (0, 0, 1),
    "blender": (2, 79, 0),
    "location": "File > Import-Export",
    "description": "Import-Export Bundler OUT format and associated files",
    "wiki_url": "https://www.github.com/stuarta0/blundle",
    "category": "Import-Export",
}

import bpy
from bpy_extras.io_utils import ExportHelper
from progress_report import ProgressReport, ProgressReportSubstep

import os
import shutil
import subprocess
from lxml import etree as ET
from math import sin, cos, tan, radians, floor
from mathutils import Vector, Matrix, Euler


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


    def create_render_scene(self, scene, clip):
        """ Creates a scene specifically for rendering source movie clip as JPG stills and infering camera data and points """
        sc = bpy.data.scenes.new('export.bundler')
        sc.frame_start = scene.frame_start
        sc.frame_end = scene.frame_end
        
        sc.objects.link(scene.camera)
        sc.camera = scene.camera
        sc.active_clip = clip
        
        r = sc.render
        r.resolution_x = clip.size[0]
        r.resolution_y = clip.size[1]
        r.resolution_percentage = floor(100 * min(1.0, (3000 / max(r.resolution_x, r.resolution_y))))  # 3000px limit on PMVS
        r.fps = scene.render.fps
        r.image_settings.file_format = 'JPEG'
        
        sc.use_nodes = True
        tree = sc.node_tree
        
        for node in tree.nodes:
            tree.nodes.remove(node)
        
        nodes = []
        
        clip_node = tree.nodes.new(type='CompositorNodeMovieClip')
        clip_node.clip = clip
        nodes.append(clip_node)
        
        # TODO: determine whether undistorting before export requires transforming the 2D coordinates too
        # undistort_node = tree.nodes.new(type='CompositorNodeMovieDistortion')
        # undistort_node.clip = clip
        # undistort_node.distortion_type = 'UNDISTORT'
        # nodes.append(undistort_node)
        
        scale_node = tree.nodes.new(type='CompositorNodeScale')
        scale_node.space = 'RENDER_SIZE'
        scale_node.frame_method = 'STRETCH'
        nodes.append(scale_node)
        
        comp_node = tree.nodes.new(type='CompositorNodeComposite')
        nodes.append(comp_node)
        
        for i in range(1, len(nodes)):
            tree.links.new(nodes[i-1].outputs[0], nodes[i].inputs[0])
        
        return sc


    def execute(self, context):
        # with ProgressReport(context.window_manager) as progress:
        if self.clip not in bpy.data.movieclips:
            self.report({'ERROR'}, 'No movie clip selected')
            return {'CANCELLED'}
        
        blend = os.path.dirname(bpy.context.blend_data.filepath)
        targetdir = os.path.dirname(self.filepath)
        
        scene = context.scene
        clip = bpy.data.movieclips[self.clip]
        
        # set up a render scene for movie clip output
        scene = self.create_render_scene(scene, clip)
        try:
            # vectors for processing vec2 marker coordinates from (0.0...1.0) bottom left to
            # absolute pixel location relative to frame centre
            # i.e. list(map(lambda i, j: i * j, list(marker.co - voffset), list(clip_size)))
            clip_size = Vector((int(scene.render.resolution_x * (scene.render.resolution_percentage / 100)),
                                int(scene.render.resolution_y * (scene.render.resolution_percentage / 100))))
            voffset = Vector((0.5, 0.5))

            tracking = clip.tracking  # tracking contains camera info, default tracker settings, stabilisation info, etc
            frames = range(scene.frame_start, scene.frame_end + 1, self.frame_step)
            cameras = []  # contains all camera data for each step of the frame range
            active_tracks = []  # contains all bundled trackers active during specified frame range

            # get the global transform for the camera without camera constraint to 
            # project the tracked points bundle into world space
            scene.frame_set(1)
            cam_constraint = scene.camera.constraints[0]
            cam_constraint.influence = 0
            mw = scene.camera.matrix_world.copy()
            cam_constraint.influence = 1

            for f in frames:
                scene.frame_set(f)
                # render the undistorted frame to file
                # Note: ensure compositor is set up to output movieclip frames only (without undistort node)
                filename = '{0:0>4}.jpg'.format(f)
                scene.render.filepath = os.path.join(targetdir, filename)
                bpy.ops.render.render(write_still=True, scene=scene.name)
                # get the unique tracks at this frame
                tracks = []
                for track in tracking.tracks:
                    if track.has_bundle and track.markers.find_frame(f):
                        tracks.append(track)
                        if track not in active_tracks:
                            active_tracks.append(track)
                # get camera transforms for this frame
                cd = scene.camera.data
                R = scene.camera.matrix_world.to_euler('XYZ').to_matrix()
                R.transpose()
                c = Vector(scene.camera.matrix_world.translation)
                t = -1 * R * c
                cameras.append({
                    'filename': filename,
                    'frame': f,
                    'focal_length': int(clip_size[0] * (cd.lens / cd.sensor_width)), # tracking.camera.focal_length_pixels,
                    'k': (tracking.camera.k1, tracking.camera.k2, tracking.camera.k3),
                    'translation': t,
                    'rotation': R,
                    'tracks': tracks,
                })
            
            # write the image list file that corresponds with the camera index in bundle.out
            with open(os.path.join(targetdir, 'list.txt'), 'w+') as f:
                f.writelines(['{}\n'.format(data['filename']) for data in cameras])

            # knock out active_tracks that appear in <2 cameras
            to_remove = []
            for track in active_tracks:
                track_cameras = []
                for camera in cameras:
                    if track in camera['tracks']:
                        track_cameras.append(camera)
                if len(track_cameras) < 2:
                    to_remove.append(track)

            for track in to_remove:
                active_tracks.remove(track)

            sift = 0
            with open(self.filepath, 'w+') as f:
                f.write('# Bundle file v0.3\n')
                f.write('{} {}\n'.format(len(cameras), len(active_tracks)))
                for camera in cameras:
                    f.write('{focal_length} {k[0]} {k[1]}\n'.format(**camera))
                    f.write('{v[0]} {v[1]} {v[2]}\n'.format(v=camera['rotation'][0]))
                    f.write('{v[0]} {v[1]} {v[2]}\n'.format(v=camera['rotation'][1]))
                    f.write('{v[0]} {v[1]} {v[2]}\n'.format(v=camera['rotation'][2]))
                    f.write('{v[0]} {v[1]} {v[2]}\n'.format(v=camera['translation']))
                # now write the points and corresponding matching cameras
                for track in active_tracks:
                    f.write('{v[0]} {v[1]} {v[2]}\n'.format(v=(mw * track.bundle)))
                    f.write('255 255 255\n')  # TODO: RGB of point
                    # calculate view list
                    track_cameras = []
                    for camera in cameras:
                        if track in camera['tracks']:
                            track_cameras.append(camera)
                    f.write('{count}'.format(count=len(track_cameras)))
                    for tc in track_cameras:
                        # The pixel positions are floating point numbers in a coordinate system where the origin is the center of the image, 
                        # the x-axis increases to the right, and the y-axis increases towards the top of the image. Thus, (-w/2, -h/2) is 
                        # the lower-left corner of the image, and (w/2, h/2) is the top-right corner (where w and h are the width and height of the image).
                        # http://www.cs.cornell.edu/~snavely/bundler/bundler-v0.4-manual.html
                        marker = track.markers.find_frame(tc['frame'])
                        f.write(' {idx} {sift} {co[0]} {co[1]}'.format(
                            idx=cameras.index(tc),
                            sift=sift,  # tc['tracks'].index(track),
                            co=list(map(lambda i, j: i * j, list(marker.co - voffset), list(clip_size)))))
                        sift += 1
                    f.write('\n')

        except Exception as ex:
            raise ex
        finally:
            # remove the temporary export scene
            bpy.data.scenes.remove(scene)
        
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
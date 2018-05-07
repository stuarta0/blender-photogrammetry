import bpy
import os
from math import floor
from mathutils import Vector, Matrix, Euler


def create_render_scene(scene, clip):
    """ Creates a scene specifically for rendering source movie clip as JPG stills """
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


def extract(properties, *args, **kwargs):
    """ Prepares a scene for export (including writing frames to <dirpath>).
    :param scene: the scene to export
    :param clip: the movieclip with tracking data
    :param filepath: the target filepath
    :param frame_range: a list of integers representing which frames to export
    :returns: {
        'resolution': (width, height),
        'trackers': { 
            id<int>: {
                'co': (x, y, z),
                'rgb': (r, g, b),
            }
        },
        'cameras': {
            id<int>: {
                'filename': str,       # relative path
                'f': float,            # focal length in pixels
                'k': (k1, k2, k3),
                't': (x, y, z),        # pmvs transformed translation
                'R': ((r00, r01, r02),
                      (r10, r11, r12),
                      (r20, r21, r22)),
                'trackers': {
                    id<int>: (x, y),   # origin in image centre
                }
            }
        }
    }
    """
    scene = kwargs.get('scene', None)
    dirpath = bpy.path.abspath(kwargs.get('dirpath', None))
    if not scene or not dirpath:
        raise Exception('Scene and dirpath not provided to blender.extract')
    
    clip = bpy.data.movieclips[properties.clip]
    frame_range = range(scene.frame_start, scene.frame_end + 1, properties.frame_step)

    # set up a render scene for movie clip output
    export_scene = create_render_scene(scene, clip)
    try:
        # vectors for processing vec2 marker coordinates from (0.0...1.0) bottom left to
        # absolute pixel location relative to frame centre
        # i.e. list(map(lambda i, j: i * j, list(marker.co - voffset), list(clip_size)))
        clip_size = Vector((int(export_scene.render.resolution_x * (export_scene.render.resolution_percentage / 100)),
                            int(export_scene.render.resolution_y * (export_scene.render.resolution_percentage / 100))))
        voffset = Vector((0.5, 0.5))

        tracking = clip.tracking  # tracking contains camera info, default tracker settings, stabilisation info, etc
        cameras = {}
        active_tracks = []  # contains all bundled trackers active during specified frame range

        # get the global transform for the camera without camera constraint to 
        # project the tracked points bundle into world space
        scene.frame_set(scene.frame_start)
        cam_constraint = scene.camera.constraints[0]
        cam_constraint.influence = 0
        mw = scene.camera.matrix_world.copy()
        cam_constraint.influence = 1

        for cid, f in enumerate(frame_range):
            # render each movie clip frame to jpeg still
            scene.frame_set(f)
            export_scene.frame_set(f)
            filename = '{0:0>4}.jpg'.format(f)
            export_scene.render.filepath = os.path.join(dirpath, filename)
            bpy.ops.render.render(write_still=True, scene=export_scene.name)

            # get the unique tracks at this frame
            tracks = []
            for track in tracking.tracks:
                if track.has_bundle and track.markers.find_frame(f):
                    tracks.append(track)
                    if track not in active_tracks:
                        active_tracks.append(track)

            # if no tracks were found at this time, skip the camera
            if not tracks:
                continue

            # get camera transforms for this frame
            cd = scene.camera.data
            R = scene.camera.matrix_world.to_euler('XYZ').to_matrix()
            R.transpose()
            c = scene.camera.matrix_world.translation.copy()
            t = -1 * R * c
            cameras.setdefault(cid, {
                'filename': filename,
                'frame': f,
                'f': int(clip_size[0] * (cd.lens / cd.sensor_width)), # tracking.camera.focal_length_pixels,
                'k': (tracking.camera.k1, tracking.camera.k2, tracking.camera.k3),
                't': tuple(t),
                'R': tuple(map(tuple, tuple(R))), # tuple(R) = (Vec3, Vec3, Vec3)
                'tracks': tracks,
                'trackers': {},
            })

        # knock out active_tracks that appear in <2 cameras
        to_remove = []
        for track in active_tracks:
            track_cameras = []
            for camera in cameras.values():
                if track in camera['tracks']:
                    track_cameras.append(camera)
            if len(track_cameras) < 2:
                to_remove.append(track)

        to_remove_cams = []
        for track in to_remove:
            active_tracks.remove(track)
            # also remove this track from any cameras and if that causes a camera to 
            # have no more tracks, remove the camera too
            for cid, camera in cameras.items():
                camera['tracks'].remove(track)
                if not camera['tracks']:
                    to_remove_cams.append(cid)
        for cid in to_remove_cams:
            cameras.pop(cid, None)

        # now build the final reference structure
        trackers = {}
        for idx, track in enumerate(active_tracks):
            trackers[idx] = {
                'co': tuple(mw * track.bundle),
                'rgb': (0, 0, 0),
            }
            # loop over every camera that this track is visible in
            track_cameras = [camera for camera in cameras.values() if track in camera['tracks']]
            for camera in track_cameras:
                # The pixel positions are floating point numbers in a coordinate system where the origin is the center of the image, 
                # the x-axis increases to the right, and the y-axis increases towards the top of the image. Thus, (-w/2, -h/2) is 
                # the lower-left corner of the image, and (w/2, h/2) is the top-right corner (where w and h are the width and height of the image).
                # http://www.cs.cornell.edu/~snavely/bundler/bundler-v0.4-manual.html
                marker = track.markers.find_frame(camera['frame'])
                camera['trackers'][idx] = tuple(map(lambda i, j: i * j, list(marker.co - voffset), list(clip_size)))
        
        # remove helper keys
        for camera in cameras.values():
            camera.pop('frame', None)
            camera.pop('tracks', None)

        # return standard format
        return {
            'resolution': tuple(map(int, clip_size)),
            'cameras': cameras,
            'trackers': trackers,
        }

    except Exception as ex:
        raise ex
    finally:
        # remove the temporary export scene
        bpy.data.scenes.remove(export_scene)
    
import bpy
import os
from math import floor
from mathutils import Vector, Matrix, Euler
import numpy as np
from .colmap.database import COLMAPDatabase


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
    r.resolution_percentage = 100
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


def export_colmap(scene, clip, filepath, frame_range):
    """ Exports a scene in COLMAP format.
    :param scene: the scene to export
    :param clip: the movieclip with tracking data
    :param filepath: the target filepath
    :param frame_range: a list of integers representing which frames to export
    """
    targetdir = os.path.dirname(filepath)

    # overwrite existing database
    if os.path.exists(filepath):
        os.remove(filepath)
        
    # colmap/scripts/database.py
    db = COLMAPDatabase.connect(filepath)
    
    # set up a render scene for movie clip output
    export_scene = create_render_scene(scene, clip)
    try:
        db.create_tables()

        # vectors for processing vec2 marker coordinates from (0.0...1.0) bottom left to
        # absolute pixel location relative to frame centre
        # i.e. list(map(lambda i, j: i * j, list(marker.co - voffset), list(clip_size)))
        clip_size = Vector((int(export_scene.render.resolution_x * (export_scene.render.resolution_percentage / 100)),
                            int(export_scene.render.resolution_y * (export_scene.render.resolution_percentage / 100))))
        voffset = Vector((0.5, 0.5))

        tracking = clip.tracking  # tracking contains camera info, default tracker settings, stabilisation info, etc
        #frames = range(scene.frame_start, scene.frame_end + 1, self.frame_step)
        cameras = []  # contains all camera data for each step of the frame range
        active_tracks = []  # contains all bundled trackers active during specified frame range

        # get the global transform for the camera without camera constraint to 
        # project the tracked points bundle into world space
        scene.frame_set(scene.frame_start)
        cam_constraint = scene.camera.constraints[0]
        cam_constraint.influence = 0
        mw = scene.camera.matrix_world.copy()
        cam_constraint.influence = 1

        for f in frame_range:
            # render each movie clip frame to jpeg still
            scene.frame_set(f)
            export_scene.frame_set(f)
            filename = '{0:0>4}.jpg'.format(f)
            export_scene.render.filepath = os.path.join(targetdir, filename)
            bpy.ops.render.render(write_still=True, scene=export_scene.name)

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
            c = scene.camera.matrix_world.translation.copy()
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

        # colmap/src/base/camera_models.h

        # // Simple camera model with one focal length and two radial distortion
        # // parameters.
        # //
        # // This model is equivalent to the camera model that Bundler uses
        # // (except for an inverse z-axis in the camera coordinate system).
        # //
        # // Parameter list is expected in the following order:
        # //
        # //    f, cx, cy, k1, k2
        # //
        # struct RadialCameraModel : public BaseCameraModel<RadialCameraModel> {
        # CAMERA_MODEL_DEFINITIONS(3, "RADIAL", 5)
        # };

        for camera in cameras:
            model1, width1, height1, params1 = \
                3, clip_size[0], clip_size[1], np.array((camera['focal_length'], clip_size[0] / 2, clip_size[1] / 2, camera['k'][0], camera['k'][1]))

            # for now just assume 1:1 camera to image (if no zoom occurs during track, we could just use 1 camera for N images)
            camera['camera_id'] = db.add_camera(3, width1, height1, params1)
            camera['image_id'] = db.add_image(camera['filename'], camera['camera_id'])

            # get all tracks visible to this camera
            keypoints = []
            tracks = [track for track in active_tracks if track in camera['tracks']]
            for track in tracks:
                # get marker coordinate for this camera's frame
                marker = track.markers.find_frame(camera['frame'])
                keypoints.append(marker.co)

            camera['keypoints'] = tracks
            db.add_keypoints(camera['image_id'], np.array(keypoints))

        # now export matches from each camera to all other cameras
        # TODO: this will do a -> b and b -> a - is this correct?
        for camera1, camera2 in zip(cameras, cameras):
            if camera1 == camera2:
                continue
            # get intesecting trackers for these two cameras
            tracks = [track for track in camera1['keypoints'] if track in camera2['keypoints']]
            # matches are 2D array of 2 columns, M rows where M is the total matches
            matches = []
            for track in tracks:
                matches.append((camera1['keypoints'].index(track), camera2['keypoints'].index(track)))
            db.add_matches(camera1['image_id'], camera2['image_id'], np.array(matches))

        db.commit()

    except Exception as ex:
        raise ex
    finally:
        # remove the temporary export scene and close the database
        bpy.data.scenes.remove(export_scene)
        db.close()
    
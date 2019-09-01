import os
import sys
import collections
import numpy as np
import struct
from .read_model import Camera, CameraModel, BaseImage, Point3D, Image

# CameraModel = collections.namedtuple(
#     "CameraModel", ["model_id", "model_name", "num_params"])
# Camera = collections.namedtuple(
#     "Camera", ["id", "model", "width", "height", "params"])
# BaseImage = collections.namedtuple(
#     "Image", ["id", "qvec", "tvec", "camera_id", "name", "xys", "point3D_ids"])
# Point3D = collections.namedtuple(
#     "Point3D", ["id", "xyz", "rgb", "error", "image_ids", "point2D_idxs"])


def write_cameras_text(path, cameras):
    """
    see: src/base/reconstruction.cc
        void Reconstruction::WriteCamerasText(const std::string& path)
        void Reconstruction::ReadCamerasText(const std::string& path)
    """
    with open(path, "w") as fid:
        fid.writelines(map(lambda line: f'{line}\n',
                           ['# Camera list with one line of data per camera:',
                            '#   CAMERA_ID, MODEL, WIDTH, HEIGHT, PARAMS[]',
                            f'# Number of cameras: {len(cameras)}']))
        fid.writelines([' '.join(map(str, [camera.id, camera.model, camera.width, camera.height] + camera.params))
                        for camera in cameras])


def write_images_text(path, images):
    """
    see: src/base/reconstruction.cc
        void Reconstruction::ReadImagesText(const std::string& path)
        void Reconstruction::WriteImagesText(const std::string& path)
    """
    with open(path, "w") as fid:
        fid.writelines(map(lambda line: f'{line}\n',
                           ['# Image list with two lines of data per image:',
                            '#   IMAGE_ID, QW, QX, QY, QZ, TX, TY, TZ, CAMERA_ID, NAME',
                            '#   POINTS2D[] as (X, Y, POINT3D_ID)',
                            f'# Number of images: {len(images)}, mean observations per image: ']))
        for image in images:
            fid.write(f'{image.id} ')
            fid.write('{} '.format(' '.join(map(str, image.qvec))))
            fid.write('{} '.format(' '.join(map(str, image.tvec))))
            fid.write(f'{image.camera_id} ')
            fid.write(f'{image.name.strip()}\n')
            for i in range(len(image.xys)):
                fid.write(f'{image.xys[i][0]} {image.xys[i][1]} {image.point3D_ids[i]} ')
            fid.write('\n')


def write_points3D_text(path, points3D):
    """
    see: src/base/reconstruction.cc
        void Reconstruction::ReadPoints3DText(const std::string& path)
        void Reconstruction::WritePoints3DText(const std::string& path)
    """
    with open(path, "w") as fid:
        fid.writelines(map(lambda line: f'{line}\n',
                           ['# 3D point list with one line of data per point:',
                            '#   POINT3D_ID, X, Y, Z, R, G, B, ERROR, TRACK[] as (IMAGE_ID, POINT2D_IDX)',
                            f'# Number of points: {len(points3D)}, mean track length: ']))
        for point in points3D:
            fid.write(f'{point.id} ')
            fid.write('{} '.format(' '.join(map(str, point.xyz))))
            fid.write('{} '.format(' '.join(map(str, point.rgb))))
            fid.write(f'{point.error} ')
            for i in range(len(point.image_ids)):
                fid.write(f'{point.image_ids[i]} {point.point2D_idxs[i]} ')
            fid.write('\n')


def write_model(path, ext, cameras, images, points3D):
    if ext == ".txt":
        write_cameras_text(os.path.join(path, "cameras" + ext), cameras)
        write_images_text(os.path.join(path, "images" + ext), images)
        write_points3D_text(os.path.join(path, "points3D") + ext, points3D)
    elif ext == '.bin':
        raise NotImplementedError('Only TXT format is currently supported.')
    else:
        raise Exception('Model must have extension .txt or .bin.')

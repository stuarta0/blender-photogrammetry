from .groups import PHOTOGRAMMETRY_PG_colmap
from .load import load
from ..utils import PhotogrammetryModule

exporter = PhotogrammetryModule('COLMAP', 'Use COLMAP to generate a dense point cloud and reconstructed mesh', PHOTOGRAMMETRY_PG_colmap, load)
binaries = ['colmap']

from .groups import PHOTOGRAMMETRY_PG_input_colmap, PHOTOGRAMMETRY_PG_output_colmap
from .extract import extract
from .load import load
from ..utils import PhotogrammetryModule

importer = PhotogrammetryModule('COLMAP', 'Read a COLMAP sparse reconstruction', PHOTOGRAMMETRY_PG_input_colmap, extract)
exporter = PhotogrammetryModule('COLMAP', 'Use COLMAP to generate a dense point cloud and reconstructed mesh', PHOTOGRAMMETRY_PG_output_colmap, load)

# a lack of corresponding binary for COLMAP will result in a bash script being generated
# binaries = ['colmap']

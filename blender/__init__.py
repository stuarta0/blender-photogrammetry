from .extract import extract
from .groups import PHOTOGRAMMETRY_PG_input_blender, PHOTOGRAMMETRY_PG_output_blender
from .load import load
from ..utils import PhotogrammetryModule

importer = PhotogrammetryModule('Blender Motion Tracking', 'Use tracking data from current scene', PHOTOGRAMMETRY_PG_input_blender, extract)
exporter = PhotogrammetryModule('Blender', 'Import data into current scene', PHOTOGRAMMETRY_PG_output_blender, load)

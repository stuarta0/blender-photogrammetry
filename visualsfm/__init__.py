from .extract import extract
from .groups import PHOTOGRAMMETRY_PG_input_visualsfm, PHOTOGRAMMETRY_PG_output_visualsfm
from .load import load
from ..utils import PhotogrammetryModule

importer = PhotogrammetryModule('VisualSfM', 'Read a VisualSfM .NVM file and associated images', PHOTOGRAMMETRY_PG_input_visualsfm, extract)
exporter = PhotogrammetryModule('VisualSfM', 'Output images and .NVM file', PHOTOGRAMMETRY_PG_output_visualsfm, load)

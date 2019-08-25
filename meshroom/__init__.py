from .extract import extract
from .groups import PHOTOGRAMMETRY_PG_meshroom
from ..utils import PhotogrammetryModule

importer = PhotogrammetryModule('Meshroom', 'Read a Meshroom structure from motion cameras.sfm file', PHOTOGRAMMETRY_PG_meshroom, extract)

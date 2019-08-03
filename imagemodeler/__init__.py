from .extract import extract
from .groups import PHOTOGRAMMETRY_PG_image_modeller
from ..utils import PhotogrammetryModule

importer = PhotogrammetryModule('ImageModeler', 'Read an ImageModeler .RZI file and associated images', PHOTOGRAMMETRY_PG_image_modeller, extract)

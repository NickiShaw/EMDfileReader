from PIL import Image
import matplotlib.pyplot as plt
import cv2
from readEMDv6 import *

# Need to fix these names to be more general/pick columns.
filter = ["Optics.Apertures.Aperture-1.Diameter", "Optics.Apertures.Aperture-2.Diameter",
          "BinaryResult.ImageSize.width", "BinaryResult.ImageSize.height",
          "BinaryResult.PixelSize.width", "BinaryResult.PixelSize.height", "BinaryResult.PixelUnitX", "BinaryResult.PixelUnitY",
          "CustomProperties.Detectors[SuperXG22].IncidentAngle.value"]

# Import file with tkinter selection.
file = GUI.select_file()
f = h5py.File(file, 'r')

plainpathname = str(file.replace('.emd', ''))

if GUI.autoProcessAsk() == "yes":

    # Export all frames to folder.
    frameExporter.saveAllFrames(f, originalfilename=plainpathname, auto=True)

    # Export important metadata to csv.
    metadata(f).getCSVmetadata(originalfilename=plainpathname, filter=None, auto=True)
else:
    # Export all frames to folder.
    frameExporter.saveAllFrames(f, originalfilename=plainpathname)

    # Export important metadata to csv.
    metadata(f).getCSVmetadata(originalfilename=plainpathname)


GUI.show_end("Finished processing.")
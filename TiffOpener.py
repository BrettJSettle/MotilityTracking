"""
@author: Brett Settle
@Department: UCI Neurobiology and Behavioral Science
@Lab: Parker Lab
@Date: August 6, 2015
"""
import tifffile
from TrackBasics import *

def read_tif():
    filename = get_filename()
    if not os.path.isfile(filename):
        raise Exception("No File Selected")
    tif=tifffile.TIFFfile(filename)
    img = np.transpose(np.squeeze(tif.asarray()), (0, 2, 1))
    return img

class TiffOpener(QThread):
    Image_Loaded_Signal = Signal()
    def __init__(self, filename=None):
        super(TiffOpener, self).__init__()
        if filename == None:
            self.filename = getFileName()
        else:
            self.filename = filename

    def run(self):
        tif = tifffile.TIFFfile(self.filename).asarray().astype(np.float32)
        self.tif = np.squeeze(tif)
        if tif.ndim == 3:
            self.tif = np.transpose(self.tif, (0, 2, 1))
        elif tif.ndim == 2:

            self.tif = np.transpose(self.tif, (1, 0))
        self.Image_Loaded_Signal.emit()
        self.terminate()

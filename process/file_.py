# -*- coding: utf-8 -*-
"""
Created on Thu Jun 26 14:43:19 2014

@author: Kyle Ellefsen
"""
from __future__ import (absolute_import, division,print_function, unicode_literals)
from future.builtins import (bytes, dict, int, list, object, range, str, ascii, chr, hex, input, next, oct, open, pow, round, super, filter, map, zip)

from PyQt4.QtCore import *
from PyQt4.QtGui import *
import pyqtgraph as pg
import pyqtgraph.exporters
import time
import os.path
import numpy as np
from skimage.io import imread, imsave
from window import Window
import global_vars as g
import codecs
import shutil, subprocess
import tifffile
import json
import re

__all__ = ['open_file_gui','open_file','save_file_gui', 'close', 'simulate_distances', 'exportMSD', 'export_distances', 'import_coords', 'export_track_lengths','set_background_image']

def open_file_gui(func, filetypes, prompt='Open File'):
    filename=g.m.filename
    if filename is not None and os.path.isfile(filename):
        filename= QFileDialog.getOpenFileName(g.m, prompt, filename, filetypes)
    else:
        filename= QFileDialog.getOpenFileName(g.m, prompt, '', filetypes)
    filename=str(filename)
    if filename != '':
        g.m.filename = filename
        func(filename)
    else:
        g.m.statusBar().showMessage('No File Selected')

def save_file_gui(func, filetypes, prompt = 'Save File'):
    filename=g.m.filename
    try:
        directory=os.path.dirname(filename)
    except:
        directory = ''
    if filename is not None and directory != '':
        filename= QFileDialog.getSaveFileName(g.m, prompt, directory, filetypes)
    else:
        filename= QFileDialog.getSaveFileName(g.m, prompt, filetypes)
    filename=str(filename)
    if filename != '':
        func(filename)
        g.m.filename = filename
    else:
        g.m.statusBar().showMessage('Save Cancelled')
            
def open_file(filename):
    g.m.statusBar().showMessage('Loading {}'.format(os.path.basename(filename)))
    t=time.time()
    Tiff=tifffile.TiffFile(filename)
    try:
        metadata=Tiff[0].image_description
        metadata = txt2dict(metadata)
    except AttributeError:
        metadata=dict()
    tif=Tiff.asarray()
    Tiff.close()
    if len(tif.shape)>3: # WARNING THIS TURNS COLOR movies TO BLACK AND WHITE BY AVERAGING ACROSS THE THREE CHANNELS
        if 'channels' in metadata.keys() and 'ImageJ' in metadata.keys():
            tif=np.transpose(tif,(0,3,2,1))
        tif=np.mean(tif,3)
    tif=np.squeeze(tif) #this gets rid of the meaningless 4th dimention in .stk files
    if len(tif.shape)==3: #this could either be a movie or a colored still frame
        if tif.shape[2]==3: #this is probably a colored still frame
            tif=np.mean(tif,2)
            tif=np.transpose(tif,(1,0)) # This keeps the x and y the same as in FIJI. 
        else:
            tif=np.transpose(tif,(0,2,1)) # This keeps the x and y the same as in FIJI. 
    elif len(tif.shape)==2: # I haven't tested whether this preserved the x y and keeps it the same as in FIJI.  TEST THIS!!
        tif=np.transpose(tif,(1,0))
    g.m.statusBar().showMessage('{} successfully loaded ({} s)'.format(os.path.basename(filename), time.time()-t))
    g.m.filename=filename
    return tif

def set_background_image(filename):
    tif = open_file(filename)
    if np.ndim(tif) == 3:
        tif = np.average(tif, 0)
    g.m.trackView.imageview.setImage(tif)
        

def txt2dict(metadata):
    meta=dict()
    try:
        metadata=json.loads(metadata.decode('utf-8'))
        return metadata
    except ValueError: #if the metadata isn't in JSON
        pass
    for line in metadata.splitlines():
        line=re.split('[:=]',line.decode())
        if len(line)==1:
            meta[line[0]]=''
        else:
            meta[line[0].lstrip().rstrip()]=line[1].lstrip().rstrip()
    return meta
    
def close(windows=None):
    '''Will close a window or a set of windows.  Takes several types as its argument:
        | 'all' (str) -- closes all windows
        | windows (list) - closes each window in the list
        | (Window) - closes individual window
        | (None) - closes current window
    '''
    if isinstance(windows,basestring):
        if windows=='all':
            windows=[window for window in g.m.windows]
            for window in windows:
                window.close()
    elif isinstance(windows,list):
        for window in windows:
            if isinstance(window,Window):
                window.close()
    elif isinstance(windows,Window):
        windows.close()
    elif windows is None:
        if g.m.currentWindow is not None:
            g.m.currentWindow.close()

def simulate_distances(filename):
    #export all distances from randomly generated XY coordinates to random Track means
    if not hasattr(g.m.trackView, 'imported'):
        print('No coordinates imported')
    g.m.statusBar().showMessage('Saving tracks to {}'.format(os.path.basename(filename)))
    coord_count = len(g.m.trackView.imported.getData()[1])
    means = g.m.trackPlot.means.getData()
    minP = (min(means[0]), min(means[1]))
    maxP = (max(means[0]), max(means[1]))
    coords = np.random.random(len(means[1]), 2) * maxP + minP
    rand_means = np.random.random(coord_count, 2) * maxP + minP
    export_distances(filenamecoords, rand_means)

def import_coords(filename):
    data = np.loadtxt(filename, skiprows=1, delimiter='\t')
    try:
        x, y = np.transpose(data)
    except:
        print('%s has more than 2 columns of values. Must import X,Y coordinates only' % filename)
    g.m.trackView.imported.setData(x=x, y=y)

def export_distances(filename, ptsA, ptsB):
    t = time.time()
    with open(filename, 'w') as outf:
        outf.write('Distances\n')
        for i, pt in enumerate(ptsA):
            for j in range(len(ptsB)):
                outf.write('%.3f\n' % np.linalg.norm(np.subtract(pt, ptsB[j])))
    g.m.statusBar().showMessage('Successfully saved simulated distances in {}'.format(time.time() - t))

def export_track_lengths(filename):
    t = time.time()
    g.m.statusBar().showMessage('Exporting Track Lengths to {}'.format(os.path.basename(filename)))
    data = np.array([tr['fr_length'] for tr in g.m.trackPlot.filtered_tracks])
    np.savetxt(filename, data, header='Frame Length', comments='', delimiter='\t')
    g.m.statusBar().showMessage('Track Lengths successfully exported ({} s)'.format(os.path.basename(filename), time.time()-t))

def exportMSD(filename):
    t = time.time()
    g.m.statusBar().showMessage('Exporting MSD to {}'.format(os.path.basename(filename)))
    d = g.m.MSDWidget.plot_data
    data = np.transpose([d['x'], d['y'], d['er']])
    np.savetxt(filename, data, header='X\tY\tError', comments='', delimiter='\t')
    g.m.statusBar().showMessage('MSD successfully exported ({} s)'.format(os.path.basename(filename), time.time()-t))


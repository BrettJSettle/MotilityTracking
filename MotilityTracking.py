# -*- coding: utf-8 -*-
"""
Created on Thu Jun 26 14:17:38 2014
updated 2015.01.27
@author: Kyle Ellefsen
"""
from __future__ import (absolute_import, division,print_function)
import dependency_check
from future.builtins import (bytes, dict, int, list, object, range, str, ascii, chr, hex, input, next, oct, pow, round, super, filter, map, zip)
import time
tic=time.time()
import os, sys
import numpy as np
from PyQt4.QtCore import * # Qt is Nokias GUI rendering code written in C++.  PyQt4 is a library in python which binds to Qt
from PyQt4.QtGui import *
from PyQt4.QtCore import pyqtSignal as Signal
from pyqtgraph import plot, show
import pyqtgraph as pg
import global_vars as g
from window import Window
from roi import load_roi, makeROI
from CDF import *
from sklearn.cluster import DBSCAN

from histogram import Histogram
from process.motility_ import *
from process.file_ import *

try:
    os.chdir(os.path.split(os.path.realpath(__file__))[0])
except NameError:
    pass

class TrackPlot(pg.PlotDataItem):
    '''
    PlotDataItem representation of a set of tracks, imported from a bin file.
    Filterable by track length, mean lag distance, and neighbor points
    '''
    tracksChanged = Signal()
    def __init__(self, *args, **kargs):
        super(TrackPlot, self).__init__()
        self.all_tracks = []
        self.filtered_tracks = []
        self.waitForUpdate = False
        self.means = pg.ScatterPlotItem()
        self.means.setVisible(False)
        self.tracks = pg.PlotDataItem()
        self.tracks.setParentItem(self)
        self.means.setParentItem(self)

    def setTracks(self, track_list):
        self.all_tracks = track_list
        self.filter()

    def filter(self):
        if self.waitForUpdate or len(self.all_tracks) == 0:
            return
        self.filtered_tracks = []
        for tr in self.all_tracks:
            if isValidTrack(tr):
                self.filtered_tracks.append(tr)

        if g.m.additionalGroupBox.isChecked() and g.m.neighborsSpin.value() > 0:
            filter_ids = get_clusters(self.filtered_tracks)
            print([i for i in filter_ids])
            self.filtered_tracks = [self.filtered_tracks[i] for i, cluster in enumerate(filter_ids) if cluster >= 0]

        self._replot()
        self.tracksChanged.emit()

    def _replot(self):
        tracks_x = []
        tracks_y = []
        mean_x = []
        mean_y = []
        connect_list = []
        for tr in self.filtered_tracks:
            tracks_x.extend(tr['x_cor'])
            tracks_y.extend(tr['y_cor'])
            mean_x.append(tr['mean_x'])
            mean_y.append(tr['mean_y'])
            connect_list.extend([1] * (len(tr['x_cor']) - 1) + [0])
        if g.m.autoFocusCheck.isChecked() and len(tracks_x) > 0 and len(tracks_y) > 0:
            g.m.trackView.imageview.view.setRange(xRange=(min(tracks_x), max(tracks_x)), yRange=(min(tracks_y), max(tracks_y)))
        self.tracks.setData(x=tracks_x, y=tracks_y, connect=np.array(connect_list))
        self.means.setData(x=mean_x, y=mean_y, symbol='x', brush=(255, 0, 0), pen=(255, 0, 0))
    
    def export(self, filename, filtered=False):
        tracks = self.all_tracks if not filtered else seld.filtered_tracks
        g.m.statusBar().showMessage('Saving tracks to {}'.format(os.path.basename(filename)))
        t = time.time()
        with open(filename, 'w') as outf:
            for tr in tracks:
                outf.write('\n'.join(['%.4f\t%.4f' % x, y in zip(tr['x_cor'], tr['y_cor'])]))
            outf.write('\n')

        g.m.statusBar().showMessage('Successfully saved tracks in {}'.format(time.time() - t))


def isValidTrack(track):
    if not g.m.MSLDGroupBox.isChecked() or g.m.MSLDMinSpin.value() <= track['mean_dis_pixel_lag'] <= g.m.MSLDMaxSpin.value():
        if g.m.minLengthSpin.value() <= track['fr_length'] <= g.m.maxLengthSpin.value():
            if not g.m.ignoreOutsideCheck.isChecked() or track_in_roi(track):
                return True
    return False

def export_real_distances(filename):

    coords = g.m.trackView.imported.getData()
    means = g.m.trackPlot.means.getData()
    if np.size(coords) == 0 or np.size(means) == 0:
        print("Must have track means and imported coordinates to export distances between them")
    else:
        export_distances(filename, means, coords)

def import_mat(mat):
    if len(mat) == 0:
        return
    g.mat = mat
    main, reject, r = create_main_data_struct(mat, g.m.MSLDMinSpin.value(), g.m.MSLDMaxSpin.value())
    g.m.trackPlot.waitForUpdate = True
    g.m.minLengthSpin.setValue(4)
    g.m.maxLengthSpin.setValue(20)
    g.m.MSLDMinSpin.setValue(0)
    g.m.MSLDMaxSpin.setValue(round(max([tr['mean_dis_pixel_lag'] for tr in main])))
    g.m.neighborDistanceSpin.setValue(round(max([max(track['dis_pixel_lag']) for track in main])))
    g.m.trackPlot.waitForUpdate = False

    g.m.trackPlot.setTracks(main)

def get_clusters(tracks):
    neighbors = g.m.neighborsSpin.value()
    dist = g.m.neighborDistanceSpin.value()
    data = np.array([[tr['mean_x'], tr['mean_y']] for tr in tracks])
    scanner = DBSCAN(eps=dist, min_samples=neighbors)
    ids = scanner.fit_predict(data)
    return ids

def track_in_roi(track):
    for roi in g.m.currentWindow.rois:
        if roi.contains(track['mean_x'], track['mean_y']):
            return True
    return False

def updateMSD(par_det):
    x, y, er = calculate_MSD_plot(par_det, [g.m.minLengthSpin.value(), g.m.maxLengthSpin.value()])
    g.m.MSDWidget.clear()
    err = pg.ErrorBarItem(x=x, y=y, top=er, bottom=er, beam=0.5)
    g.m.MSDWidget.plot_data = {'er': er, 'x': x, 'y': y}
    g.m.MSDWidget.addItem(err)
    msd = pg.PlotDataItem(x = x, y = y, pen = (0, 255, 0))
    g.m.MSDWidget.addItem(msd)

def updateHistogram(tracks):
    mean_dists = np.array([tr['mean_dis_pixel_lag'] for tr in tracks])
    g.m.histogram.setData(mean_dists)

def update_plots():
    tracks = g.m.trackPlot.filtered_tracks
    updateHistogram(tracks)
    updateMSD(tracks)
    g.m.CDFWidget.setTracks(tracks)
    # update MSD, histogram, and CDF? with new filtered tracks


def initializeMainGui():
    g.init('gui/MotilityTracking.ui')
    g.m.trackView = Window(np.zeros((3, 3, 3)))
    g.m.histogram = Histogram(title='Mean Single Lag Distance Histogram', labels={'left': 'Count', 'bottom': 'Mean SLD Per Track (Pixels)'})
    g.m.trackPlot = TrackPlot()
    g.m.trackPlot.tracksChanged.connect(update_plots)
    g.m.trackView.imageview.addItem(g.m.trackPlot)
    g.m.trackView.imported = pg.ScatterPlotItem()
    g.m.trackView.imageview.addItem(g.m.trackView.imported)

    g.m.actionImportBin.triggered.connect(lambda : open_file_gui(lambda f: import_mat(open_bin(f)),  prompt='Import .bin file of tracks', filetypes='*.bin'))
    g.m.actionImportBackground.triggered.connect(lambda : open_file_gui(set_background_image,  prompt='Select tif file as background image', filetypes='*.tif *.tiff *.stk'))
    g.m.actionImportCoordinates.triggered.connect(lambda : open_file_gui(import_coords, prompt='Import coordinates from txt file', filetypes='*.txt'))
    g.m.actionSimulateDistances.triggered.connect(lambda : save_file_gui(simulate_distances, prompt = 'Save simulated distances', filetypes='*.txt'))
    g.m.actionExportMSD.triggered.connect(lambda : save_file_gui(exportMSD, prompt='Export Mean Squared Displacement Values', filetypes='*.txt'))
    g.m.actionExportHistogram.triggered.connect(lambda : save_file_gui(g.m.histogram.export, prompt='Export Histogram Values', filetypes='*.txt'))
    g.m.actionExportTrackLengths.triggered.connect(lambda : save_file_gui(export_track_lengths, prompt='Export Track Lengths', filetypes='*.txt'))
    g.m.actionExportOutlined.triggered.connect(lambda : g.m.trackPlot.export(filtered=True))
    g.m.actionExportDistances.triggered.connect(lambda : save_file_gui(export_real_distances,  prompt='Export Distances', filetypes='*.txt'))
    
    g.m.MSLDMinSpin.setOpts(value=0, decimals=2, maximum=1000)
    g.m.MSLDMaxSpin.setOpts(value=100, decimals=2, maximum=1000)
    g.m.neighborsSpin.setOpts(value=0, maximum=100, int=True, step=1)
    g.m.neighborDistanceSpin.setOpts(value=1, decimals=2, maximum=100)
    g.m.minLengthSpin.setOpts(value=4, maximum=1000, int=True, step=1)
    g.m.maxLengthSpin.setOpts(value=20, maximum=1000, int=True, step=1)

    g.m.MSLDGroupBox.toggled.connect(g.m.trackPlot.filter)
    g.m.additionalGroupBox.toggled.connect(g.m.trackPlot.filter)
    g.m.MSLDMaxSpin.sigValueChanged.connect(g.m.trackPlot.filter)
    g.m.MSLDMinSpin.sigValueChanged.connect(g.m.trackPlot.filter)
    g.m.neighborDistanceSpin.sigValueChanged.connect(g.m.trackPlot.filter)
    g.m.neighborsSpin.sigValueChanged.connect(g.m.trackPlot.filter)
    g.m.minLengthSpin.sigValueChanged.connect(g.m.trackPlot.filter)
    g.m.maxLengthSpin.sigValueChanged.connect(g.m.trackPlot.filter)
    g.m.hideBackgroundCheck.toggled.connect(lambda v: g.m.trackView.imageview.getImageItem().setVisible(not v))
    g.m.ignoreOutsideCheck.toggled.connect(g.m.trackPlot.filter)
    g.m.plotMeansCheck.toggled.connect(g.m.trackPlot.means.setVisible)
    g.m.plotTracksCheck.toggled.connect(g.m.trackPlot.tracks.setVisible)

    g.m.viewTab.layout().insertWidget(0, g.m.trackView)

    g.m.MSDWidget = pg.PlotWidget(title='Mean Squared Displacement Per Lag', labels={'left': 'Mean Squared Disance (p^2)', 'bottom': 'Lag Count'})
    g.m.analysisTab.layout().addWidget(g.m.MSDWidget)
    
    g.m.analysisTab.layout().addWidget(g.m.histogram)

    g.m.CDFWidget = CDFWidget()#pg.PlotWidget(title = 'Cumulative Distribution Function', labels={'left': 'Cumulative Probability', 'bottom': 'Single Lag Displacement Squared'})
    #g.m.CDFPlot = pg.PlotCurveItem()
    g.m.cdfTab.layout().addWidget(g.m.CDFWidget)

    g.m.installEventFilter(mainWindowEventEater)
    g.m.setWindowTitle('Motility Tracking')
    g.m.show()


class MainWindowEventEater(QObject):
    def __init__(self,parent=None):
        QObject.__init__(self,parent)
    def eventFilter(self,obj,event):
        if (event.type()==QEvent.DragEnter):
            if event.mimeData().hasUrls():
                event.accept()   # must accept the dragEnterEvent or else the dropEvent can't occur !!!
            else:
                event.ignore()
        if (event.type() == QEvent.Drop):
            if event.mimeData().hasUrls():   # if file or link is dropped
                url = event.mimeData().urls()[0]   # get first url
                filename=url.toString()
                filename=filename.split('file:///')[1]
                print('filename={}'.format(filename))
                import_mat(bin2mat(filename))  #This fails on windows symbolic links.  http://stackoverflow.com/questions/15258506/os-path-islink-on-windows-with-python
                g.m.setWindowTitle('Motility Tracking - ' + filename)
                event.accept()
            else:
                event.ignore()
        return False # lets the event continue to the edit
mainWindowEventEater = MainWindowEventEater()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    initializeMainGui()
    
    insideSpyder='SPYDER_SHELL_ID' in os.environ
    if not insideSpyder: #if we are running outside of Spyder
        sys.exit(app.exec_()) #This is required to run outside of Spyder
    
    
    
    
    
    
    
    

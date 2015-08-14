"""
@author: Brett Settle
@Department: UCI Neurobiology and Behavioral Science
@Lab: Parker Lab
@Date: August 6, 2015
"""
from math import sqrt
import numpy as np
from PyQt4.QtCore import *
from PyQt4.QtCore import pyqtSignal as Signal
from PyQt4.QtGui import *
import pyqtgraph as pg
pg.setConfigOptions(useWeave=False)
from TrackGlobals import *
import xlrd, xlwt
import os

last_file = ''

def getFileName(multiple=False, **args):
    global last_file
    if multiple:
        filenames = [str(i) for i in QFileDialog.getOpenFileNames(directory=os.path.dirname(last_file), **args)]
        last_file = filenames[0]
        return filenames
    filename = str(QFileDialog.getOpenFileName(directory=os.path.dirname(last_file), **args))
    last_file = filename
    return filename

def getSaveFileName(info='data', **args):
    filename = last_file[:-4] +"_" + info
    savename = str(QFileDialog.getSaveFileName(directory = filename, **args))
    return savename

def distance(ptA, ptB):
    return sqrt((ptA[0]-ptB[0])**2 + (ptA[1]-ptB[1])**2)

def mean(vals):
    return sum(vals) / float(len(vals))

def bytes_from_file(filename, chunksize=72):
    with open(filename, "rb") as f:
        while True:
            chunk = f.read(chunksize)
            if chunk:
                for b in chunk:
                    yield b
            else:
                break

from functools import reduce

def correct_blinking(tracks, temporal, spatial):
    new_tracks = []
    init = 0
    while init < len(tracks):
        cur = {init}
        tr1 = tracks[init]
        for i in range(init+1, len(tracks)):
            tr2 = tracks[i]
            if min(tr2['frame']) - max(tr1['frame']) > temporal:
                break
            elif distance((tr1['xmean'], tr1['ymean']), (tr2['xmean'], tr2['ymean'])) <= spatial:
                cur.add(i)
        new_tracks.append(cur)
        init += 1
        cur = {init}

    first = new_tracks[::-1]
    second = map(lambda a: a | reduce(lambda b, c: b | c, filter(lambda d: d & a, first)), first)
    while second != first:
        first = second
        second = map(lambda a: a | reduce(lambda b, c: b | c, filter(lambda d: d & a, first)), first)
    second = np.unique([tuple(a) for a in second])
    tracks = [join_tracks([tracks[i] for i in links]) for links in second]
    with open('outfile.txt', 'w') as outf:
        outf.write('\n\n'.join([("%s:\t%s" % (k, v)) for k, v in tracks[100].items()]))
    return tracks

def join_tracks(tracks):
    tracks = sorted(tracks, key = lambda t: t['frame'][0])
    while len(tracks) > 1:
        for k in tracks[0]:
            if k == 'link':
                tracks[0][k] = tracks[0][k][:-1] + tracks[1][k]
            if k == 'length':
                tracks[0][k][0] += tracks[1][k][1]
                tracks[0][k].extend(tracks[1][k][1:])
            elif isinstance(tracks[0][k], list):
                tracks[0][k].extend(tracks[1][k][1:])
            elif isinstance(tracks[0][k], (np.generic, float, int)):
                tracks[0][k] = mean([tracks[0][k], tracks[1][k]])
        del tracks[1]
    return tracks[0]

class DistanceSaver(QThread):
    DoneSignal = Signal()
    def __init__(self, mean_XYs, maxDist=None, info=''):
        self.pts = zip(*mean_XYs)
        self.maxDist = maxDist
        super(DistanceSaver, self).__init__()
        self.filename = getSaveFileName(caption='Save distances to a file...', filter="Text file (*.txt)", info=info)
    def run(self):
        with open(self.filename, 'w') as out_file:
            for i in range(len(self.pts)):
                for j in range(i+1, len(self.pts)):
                    d = distance(self.pts[i], self.pts[j])
                    if self.maxDist == None or d <= self.maxDist:
                        out_file.write("%.3f\n" % d)
        self.DoneSignal.emit()


class DistanceMapSaver(QThread):
    DoneSignal = Signal()
    def __init__(self, to_map, map_to, info=''):
        super(DistanceMapSaver, self).__init__()
        self.filename = getSaveFileName(caption='Save distances from Track mean XYs to FLIKA points...', filter="Text file (*.txt)", info=info)
        self.map_to = map_to
        self.pairs = [{'start': pt, 'distance': 0} for pt in to_map]
    def run(self):
        # create dict of all track means, to map with closest FLIKA
        for pair in self.pairs:
            for xy in self.map_to:
                dist = distance(pair['start'], xy)
                if pair['distance'] == 0 or dist < pair['distance']:
                    pair['distance'] = dist
        with open(self.filename, 'w') as outf:
            for pair in self.pairs:
                outf.write("%.4f\n" % pair['distance'])

        self.DoneSignal.emit()

class Struct():
    def __init__(self, **args):
        self.__dict__.update(args)

    def __setattr__(self, k, v):
        self.__dict__[k] = v

def create_main_data_struct(mlist, ltl, utl):
    '''
    July 21 2014
    Brett Settle, translated from Divya
    Take mlist and create main structure
    returns par_det and reject_track
    '''

    par_det = []
    reject_track = []

    nmol = len(mlist)
    jk = rt = 0
    for i in range(nmol):
        index = np.size(mlist[i]['x'], 0)

        if index > ltl and index <= utl:
            jk += 1
            par_det.append(Struct(num=i))
            par_det[-1].firstframe = mlist[i]['frame'][0]
            par_det[-1].fr_length = np.size(mlist[i]['selfframe'][1:], 0)
            par_det[-1].frames = mlist[i]['selfframe'][1:]
            pos_x = mlist[i]['x'][1:index+1]
            pos_y = mlist[i]['y'][1:index+1]
            par_det[-1].x_cor = pos_x
            par_det[-1].y_cor = pos_y
            par_det[-1].mean_x = mean(pos_x)
            par_det[-1].mean_y = mean(pos_y)
            par_det[-1].inst_vel = np.zeros((len(pos_x)-1))
            par_det[-1].dis_pixel_lag = np.zeros((len(pos_x)-1))
            for j in range(len(pos_x)-1):
                par_det[-1].inst_vel[j] = (sqrt((pos_x[j+1]-pos_x[j])**2+(pos_y[j+1]-pos_y[j])**2))
                par_det[-1].dis_pixel_lag[j]=(sqrt((pos_x[j+1]-pos_x[j])**2+(pos_y[j+1]-pos_y[j])**2))
            par_det[-1].mean_vel = mean(par_det[-1].inst_vel)
            par_det[-1].mean_dis_pixel_lag = mean(par_det[-1].dis_pixel_lag)
            Nt = len(pos_x)-1
            par_det[-1].lag_num = np.zeros((Nt))
            par_det[-1].dist_sqr = [None] * (Nt)
            par_det[-1].mean_dist_sqr = np.zeros((Nt))
            for n in range(1, Nt+1):
                par_det[-1].lag_num[n-1] = n
                Na = Nt - n + 1
                sp = 1
                par_det[-1].dist_sqr[n-1] = np.zeros((Na))
                for j in range(1, Na+1):
                    par_det[-1].dist_sqr[n-1][j-1] = (pos_x[sp+n-1]-pos_x[sp-1])**2+(pos_y[sp+n-1]-pos_y[sp-1])**2 # Caluclating MSD in pixels
                    sp+=1
                proxy_mean = par_det[-1].dist_sqr[n-1]
                proxy_mean = proxy_mean[proxy_mean != 0]
                par_det[-1].mean_dist_sqr[n-1] = mean(proxy_mean) if len(proxy_mean) != 0 else np.nan

        elif index > utl:
            rt += 1
            reject_track.append(Struct(num=i))
            reject_track[-1].x_cor=mlist[i]['x'][1:]
            reject_track[-1].y_cor=mlist[i]['y'][1:]
            reject_track[-1].ff=mlist[i]['frame'][0]
            reject_track[-1].length = index

    return par_det, reject_track, rt

def read_locations(filename, columns):
    workbook = xlrd.open_workbook(filename)
    worksheet = workbook.sheet_by_name('Puff Data')
    returns = {}
    for i in range(worksheet.ncols):
        title = worksheet.cell_value(0, i)
        if title in columns.keys():
            returns[columns[title]] = [val for val in worksheet.col_values(i, 1) if val != '']
    return returns

class TrackGraphItem(QGraphicsPathItem):
    def __init__(self, tracks, **args):
        """tracks is a dict, with x and y arguments"""
        self.tracks = tracks
        if len(tracks) == 0:
            self.path = None
        else:
            self.path = self.make_path()
        QGraphicsPathItem.__init__(self, self.path, **args)
        self.setPen(pg.mkPen('g'))

    def make_path(self):
        connect = np.array([], dtype=bool)
        x = np.array([])
        y = np.array([])
        for tr in self.tracks:
            connect = np.append(connect, [1] * (len(tr['x'])-1) + [0]) # don't draw the segment between each trace
            x = np.append(x, tr['x'])
            y = np.append(y, tr['y'])
        return pg.arrayToQPath(x, y, connect)

    def set_tracks(self, tracks):
        self.tracks = tracks
        self.setPath(self.make_path())

    def shape(self): # override because QGraphicsPathItem.shape is too expensive.
        return QGraphicsItem.shape(self)
    def boundingRect(self):
        return self.path.boundingRect()

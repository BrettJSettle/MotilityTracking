
from __future__ import (absolute_import, division,print_function)
from future.builtins import (bytes, dict, int, list, object, range, str, ascii, chr, hex, input, next, oct, pow, round, super, filter, map, zip)

import numpy as np
import pyqtgraph as pg
import sys, os, time
import global_vars as g
from PyQt4.QtGui import *
from PyQt4.QtCore import *
import time
from process.import_insight import bin2mat
# MList will be one array of (structures of arrays)


def open_bin(filename):
    g.m.statusBar().showMessage('Loading {}'.format(os.path.basename(filename)))
    g.m.filename=filename
    t = time.time()
    mat = bin2mat(filename)
    g.m.statusBar().showMessage('{} successfully loaded ({} s)'.format(os.path.basename(filename), time.time()-t))
    g.m.setWindowTitle('Motility Tracking - ' + filename)
    return mat
    


def create_main_data_struct(mlist, ltl, utl):
    '''
    July 21 2014
    Brett Settle, translated from Divya
    Take mlist, low track length, and upper track length and create main structure
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
            to_add = {'num': i}
            to_add['firstframe'] = mlist[i]['frame'][0]
            to_add['fr_length'] = np.size(mlist[i]['selfframe'][1:], 0)
            to_add['frames'] = mlist[i]['selfframe'][1:]
            pos_x = mlist[i]['x'][1:index+1]
            pos_y = mlist[i]['y'][1:index+1]
            to_add['x_cor'] = pos_x
            to_add['y_cor'] = pos_y
            to_add['mean_x'] = np.mean(pos_x)
            to_add['mean_y'] = np.mean(pos_y)
            to_add['inst_vel'] = np.zeros((len(pos_x)-1))
            to_add['dis_pixel_lag'] = np.zeros((len(pos_x)-1))
            for j in range(len(pos_x)-1):
                to_add['inst_vel'][j] = (np.sqrt((pos_x[j+1]-pos_x[j])**2+(pos_y[j+1]-pos_y[j])**2))
                to_add['dis_pixel_lag'][j]=(np.sqrt((pos_x[j+1]-pos_x[j])**2+(pos_y[j+1]-pos_y[j])**2))
            to_add['mean_vel'] = np.mean(to_add['inst_vel'])
            to_add['mean_dis_pixel_lag'] = np.mean(to_add['dis_pixel_lag'])
            Nt = len(pos_x)-1
            to_add['lag_num'] = np.zeros((Nt))
            to_add['dist_sqr'] = [None] * (Nt)
            to_add['mean_dist_sqr'] = np.zeros((Nt))
            for n in range(1, Nt+1):
                to_add['lag_num'][n-1] = n
                Na = Nt - n + 1
                sp = 1
                to_add['dist_sqr'][n-1] = np.zeros((Na))
                for j in range(1, Na+1):
                    to_add['dist_sqr'][n-1][j-1] = (pos_x[sp+n-1]-pos_x[sp-1])**2+(pos_y[sp+n-1]-pos_y[sp-1])**2 # Caluclating MSD in pixels
                    sp+=1
                proxy_mean = to_add['dist_sqr'][n-1]
                proxy_mean = proxy_mean[proxy_mean != 0]
                to_add['mean_dist_sqr'][n-1] = np.mean(proxy_mean) if len(proxy_mean) != 0 else np.nan
            par_det.append(to_add)
        elif index > utl:
            rt += 1
            to_reject = {'num':i}
            to_reject['x_cor']=mlist[i]['x'][1:]
            to_reject['y_cor']=mlist[i]['y'][1:]
            to_reject['ff']=mlist[i]['frame'][0]
            to_reject['length'] = index
            reject_track.append(to_reject)

    return par_det, reject_track, rt

def calculate_MSD_plot(tracks, lag_range):
    distances_sq_by_lag = [ [] for i in range(10) ] 
    for i in range(len(tracks)):
        x = tracks[i]['x_cor']
        y = tracks[i]['y_cor']
        nLags=len(x)
        if lag_range[0]<=nLags<=lag_range[1]:
            for i in np.arange(nLags):
                for j in np.arange(nLags):
                    if j>=i:
                        distance_sq=(x[i]-x[j])**2+(y[i]-y[j])**2
                        while len(distances_sq_by_lag)<=j-i:
                            distances_sq_by_lag.append([])
                        distances_sq_by_lag[j-i].append(distance_sq)
    
    lags     =  np.arange(len(distances_sq_by_lag))
    means    =  np.array([ np.mean(distances_sq_by_lag[lag])                      for lag in lags])
    counts   =  np.array([     len(distances_sq_by_lag[lag])                      for lag in lags])
    std_errs =  np.array([  np.std(distances_sq_by_lag[lag])/np.sqrt(counts[lag]) for lag in lags])
    return lags, means, std_errs

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

if __name__=='__main__':
    #infile=r'C:/Users/kyle/Desktop/test2.bin'
    #infile=r'Z:\2016_01_27_paMCherry_ITPR_hemi_glial\2016_02_11_kyle_analysis\trial_8.bin'
    infile=r'C:\Users\kyle\Desktop\test_insight.bin'
    
    
    
    
    
    
    
    
    
    
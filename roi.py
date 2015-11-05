# -*- coding: utf-8 -*-
"""
Created on Fri Jul 18 18:10:04 2014

@author: Kyle Ellefsen
"""
from PyQt4.QtCore import *
from PyQt4.QtGui import *
import global_vars as g
import pyqtgraph as pg
from skimage.draw import polygon, line
import numpy as np
import os
import time


class ROI(QWidget):
    " This is an ROI.  I need to document it better."
    translated=Signal()
    translate_done=Signal()
    deleteSignal=Signal()
    kind='freehand'
    def __init__(self,window,x,y):
        QWidget.__init__(self)
        self.window=window
        self.window.currentROI=self
        self.view=self.window.imageview.view
        self.path=QPainterPath(QPointF(x,y))
        self.pathitem=QGraphicsPathItem(self.view)
        self.color=Qt.yellow
        self.pathitem.setPen(QPen(self.color))
        self.pathitem.setPath(self.path)
        self.view.addItem(self.pathitem)
        self.mouseIsOver=False
        self.createActions()
        self.beingDragged=False
        self.window.deleteButtonSignal.connect(self.deleteCurrentROI)
        self.window.closeSignal.connect(self.delete)

    def extend(self,x,y):
        self.path.lineTo(QPointF(x,y))
        self.pathitem.setPath(self.path)

    def deleteCurrentROI(self):
        if self.window.currentROI is self:
            self.delete()

    def getTraceWindow(self):
        trace_with_roi = [t for t in g.m.traceWindows if t.hasROI(self)]
        if len(trace_with_roi) == 1:
            return trace_with_roi[0]
        return False

    def delete(self):
        for roi in self.linkedROIs:
            roi.linkedROIs.remove(self)
        if self in self.window.rois:
            self.window.rois.remove(self)
        self.window.currentROI=None
        self.view.removeItem(self.pathitem)
        trace = self.getTraceWindow()
        if trace:
            a=set([r['roi'] for r in trace.rois])
            b=set(self.window.rois)
            if len(a.intersection(b))==0:
                trace.indexChanged.disconnect(self.window.setIndex)
            trace.removeROI(self)
    def getPoints(self):
        points=[]
        for i in np.arange(self.path.elementCount()):
            e=self.path.elementAt(i)
            x=int(np.round(e.x)); y=int(np.round(e.y))
            if len(points)==0 or points[-1]!=(x,y):
                points.append((x,y))
        self.pts=points
        self.minn=np.min(np.array( [np.array([p[0],p[1]]) for p in self.pts]),0)
        return self.pts
    def getArea(self):
        self.getMask()
        return len(self.mask)
        #cnt=np.array([np.array([np.array([p[1],p[0]])]) for p in self.pts ])
        #area = cv2.contourArea(cnt)
        #return area
    def drawFinished(self):
        self.path.closeSubpath()
        self.draw_from_points(self.getPoints()) #this rounds all the numbers down
        self.window.rois.append(self)
        self.getMask()

    def mouseOver(self,x,y):
        if self.mouseIsOver is False and self.contains(x,y):
            self.mouseIsOver=True
            self.pathitem.setPen(QPen(Qt.red))
        elif self.mouseIsOver and self.contains(x,y) is False:
            self.mouseIsOver=False
            self.pathitem.setPen(QPen(self.color))

    def contextMenuEvent(self, event):
        self.menu = QMenu(self)
        self.menu.addAction(self.copyAct)
        self.menu.addAction(self.deleteAct)
        self.menu.addAction(self.saveAct)
        self.menu.exec_(event.screenPos().toQPoint())

    def copy(self):
        g.m.clipboard=self

    def save(self,filename):
        text=''
        for roi in g.m.currentWindow.rois:
            pts=roi.getPoints()
            text+=type(roi).kind+'\n'
            for pt in pts:
                text+="{0:<4} {1:<4}\n".format(pt[0],pt[1])
            text+='\n'
        f=open(filename,'w')
        f.write(text)
        f.close()

    def save_gui(self):
        filename=g.m.settings['filename']
        if filename is not None and os.path.isfile(filename):
            filename= QFileDialog.getOpenFileName(g.m, 'Save ROI', filename, "*.txt")
        else:
            filename= QFileDialog.getOpenFileName(g.m, 'Save ROI', '', '*.txt')
        filename=str(filename)
        if filename != '':
            self.save(filename)
        else:
            g.m.statusBar().showMessage('No File Selected')
            
    def createActions(self):
        self.copyAct = QAction("&Copy", self, triggered=self.copy)
        self.deleteAct = QAction("&Delete", self, triggered=self.delete)
        self.saveAct = QAction("&Save",self,triggered=lambda : self.save_gui)
                
    def contains(self,x,y):
        return self.path.contains(QPointF(x,y))
    def translate(self,difference,startpt):
        self.path.translate(difference)
        self.pathitem.setPath(self.path)
        for roi in self.linkedROIs:
            roi.draw_from_points(self.getPoints())
            roi.translated.emit()
        self.translated.emit()
    def finish_translate(self):
        for roi in self.linkedROIs:
            roi.draw_from_points(self.getPoints())
            roi.translate_done.emit()
            roi.beingDragged=False
        self.draw_from_points(self.getPoints())
        self.getMask()
        self.translate_done.emit()
        self.beingDragged=False
    def draw_from_points(self,pts):
        self.pts=pts
        self.path=QPainterPath(QPointF(pts[0][0],pts[0][1]))
        for i in np.arange(len(pts)-1)+1:        
            self.path.lineTo(QPointF(pts[i][0],pts[i][1]))
        self.pathitem.setPath(self.path)
        
    def getMask(self):
        pts=self.pts
        tif=self.window.image
        x=np.array([p[0] for p in pts])
        y=np.array([p[1] for p in pts])
        nDims=len(tif.shape)
        if nDims==4: #if this is an RGB image stack
            tif=np.mean(tif,3)
            mask=np.zeros(tif[0,:,:].shape,np.bool)
        elif nDims==3:
            mask=np.zeros(tif[0,:,:].shape,np.bool)
        if nDims==2: #if this is a static image
            mask=np.zeros(tif.shape,np.bool)
            
        xx,yy=polygon(x,y,shape=mask.shape)
        mask[xx,yy]=True
        pts_plus=np.array(np.where(mask)).T
        for pt in pts_plus:
            if not self.path.contains(QPointF(pt[0],pt[1])):
                mask[pt[0],pt[1]]=0
        self.minn=np.min(np.array( [np.array([p[0],p[1]]) for p in self.pts]),0)
        self.mask=np.array(np.where(mask)).T-self.minn
        
def makeROI(kind,pts,window=None):
    if window is None:
        window=g.m.currentWindow
    if kind=='freehand':
        roi=ROI(window,0,0)
    elif kind=='rectangle':
        roi=ROI_rectangle(window,0,0)
    elif kind=='line':
        roi=ROI_line(window,0,0)
    else:
        print("ERROR: THIS TYPE OF ROI COULD NOT BE FOUND: {}".format(kind))
        return None
    roi.draw_from_points(pts)
    roi.drawFinished()
    return roi
def load_roi(filename):
    f = open(filename, 'r')
    text=f.read()
    f.close()
    kind=None
    pts=None
    for line in text.split('\n'):
        if kind is None:
            kind=line
            pts=[]
        elif line=='':
            makeROI(kind,pts)
            kind=None
            pts=None
        else:
            pts.append(tuple(int(i) for i in line.split()))      
    
    
    
    
    
    
    
    
    
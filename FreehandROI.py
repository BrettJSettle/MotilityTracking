"""
@author: Brett Settle
@Department: UCI Neurobiology and Behavioral Science
@Lab: Parker Lab
@Date: August 6, 2015
"""
from PyQt4.QtCore import *
from PyQt4.QtGui import *
import pyqtgraph as pg
import numpy as np
import cv2
import os


class FreehandROI(QWidget):
    " This is an ROI.  I need to document it better."
    translated=Signal()
    translate_done=Signal()
    deleteSignal=Signal()
    eraseInsideSignal = Signal()
    drawn = False
    def __init__(self,view, x, y):
        QWidget.__init__(self)
        self.view=view
        self.path=QPainterPath(QPointF(x,y))
        self.pathitem=QGraphicsPathItem(self.view)
        self.color=Qt.yellow
        self.pathitem.setPen(QPen(self.color))
        self.pathitem.setPath(self.path)
        self.view.addItem(self.pathitem)
        self.mouseIsOver=False
        self.createActions()
        self.beingDragged=False
        self.colorDialog=QColorDialog()
        self.colorDialog.colorSelected.connect(self.colorSelected)
    def extend(self,x,y):
        self.path.lineTo(QPointF(x,y))
        self.pathitem.setPath(self.path)
    def delete(self):
        self.view.removeItem(self.pathitem)
        self.deleteSignal.emit()
        self.drawn = False
    def getPoints(self):
        points=[]
        for i in np.arange(self.path.elementCount()):
            e=self.path.elementAt(i)
            x=int(np.round(e.x)); y=int(np.round(e.y))
            if len(points)==0 or points[-1]!=(x,y):
                points.append((x,y))
        self.pts=points
        return self.pts
    def getArea(self):
        cnt=np.array([np.array([np.array([p[1],p[0]])]) for p in self.pts ])
        area = cv2.contourArea(cnt)
        return area
    def drawFinished(self):
        self.path.closeSubpath()
        self.draw_from_points(self.getPoints()) #this rounds all the numbers down
        if self.getArea()<1:
            self.delete()
        self.drawn = True
    def mouseOver(self,x,y):
        if self.mouseIsOver is False and self.contains(x,y):
            self.mouseIsOver=True
            self.pathitem.setPen(QPen(Qt.red))
        elif self.mouseIsOver and self.contains(x,y) is False:
            self.mouseIsOver=False
            self.pathitem.setPen(QPen(self.color))
    def contextMenuEvent(self, event):
        self.menu = QMenu(self)
        self.menu.addAction(self.colorAct)
        self.menu.addAction(self.deleteAct)
        self.menu.addAction(self.eraseInsideAct)
        self.menu.exec_(event.screenPos().toQPoint())

    def changeColor(self):
        self.colorDialog.open()

    def colorSelected(self, color):
        if color.isValid():
            self.color=QColor(color.name())
            self.pathitem.setPen(QPen(self.color))
            self.translate_done.emit()

    def createActions(self):
        self.colorAct = QAction("&Change Color",self,triggered=self.changeColor)
        self.deleteAct = QAction("&Delete", self, triggered=self.delete)
        self.eraseInsideAct = QAction('&Erase Tracks in ROI', self, triggered=self.eraseInsideSignal.emit)

    def contains(self,x,y):
        return self.path.contains(QPointF(x,y))
    def translate(self,difference,startpt):
        self.path.translate(difference)
        self.pathitem.setPath(self.path)
        self.translated.emit()
    def finish_translate(self):
        self.draw_from_points(self.getPoints())
        self.translate_done.emit()
        self.beingDragged=False
    def draw_from_points(self,pts):
        self.path=QPainterPath(QPointF(pts[0][0],pts[0][1]))
        for i in np.arange(len(pts)-1)+1:
            self.path.lineTo(QPointF(pts[i][0],pts[i][1]))
        self.pathitem.setPath(self.path)

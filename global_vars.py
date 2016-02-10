# -*- coding: utf-8 -*-
"""
Created on Tue Jul 01 11:28:38 2014

@author: Kyle Ellefsen
"""
from PyQt4 import uic
from PyQt4.QtCore import * # Qt is Nokias GUI rendering code written in C++.  PyQt4 is a library in python which binds to Qt
from PyQt4.QtGui import *
from PyQt4.QtCore import pyqtSignal as Signal
import pyqtgraph as pg
from window import Window
import numpy as np



class SetCurrentWindowSignal(QWidget):
	sig=Signal()
	def __init__(self,parent):
		QWidget.__init__(self,parent)
		self.hide()

def init(filename):
	global m
	m=uic.loadUi(filename)
	m.windowSelectedSignal=SetCurrentWindowSignal(m)
	m.filename = ''
	
	m.clipboard = None
	m.setAcceptDrops(True)

# -*- coding: utf-8 -*-
"""
Created on Tue Jul 01 11:28:38 2014

@author: Kyle Ellefsen
"""
from PyQt4 import uic
from PyQt4.QtCore import * # Qt is Nokias GUI rendering code written in C++.  PyQt4 is a library in python which binds to Qt
from PyQt4.QtGui import *
from PyQt4.QtCore import pyqtSignal as Signal
import sys, os
if sys.version_info.major==2:
	import cPickle as pickle # pickle serializes python objects so they can be saved persistantly.  It converts a python object into a savable data structure
else:
	import pickle
from os.path import expanduser
import numpy as np
from pyqtgraph.dockarea import *
from window import Window

def mainguiClose(event):
	global m
	windows=m.windows[:]
	for window in windows:
		window.close()
	if m.scriptEditor is not None:
		m.scriptEditor.close()
	event.accept() # let the window close

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
	
	m.windows = []
	m.traceWindows = []
	m.currentWindow = None
	m.currentTrace = None

	m.clipboard = None
	m.scriptEditor = None
	m.setAcceptDrops(True)
	m.onClose = mainguiClose
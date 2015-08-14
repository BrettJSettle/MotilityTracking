"""
@author: Brett Settle
@Department: UCI Neurobiology and Behavioral Science
@Lab: Parker Lab
@Date: August 6, 2015
"""
from TrackBasics import *
from pyqtgraph.dockarea import *
from TiffOpener import TiffOpener
from FreehandROI import *
from OptionsWindow import OptionsWidget

class TracksDock(Dock):
	creatingROI = False
	openSignal = Signal()
	tracksChanged = Signal()
	def __init__(self, parent, *args, **kargs):
		self.loaded = False
		self.rois = []
		self.currentROI = None
		self.currentROIs = []
		super(TracksDock, self).__init__(*args, **kargs)
		self.all_tracks = []
		self.background_processes = []
		## Create a grid layout to manage the widgets size and position
		self.status = parent.statusBar()
		self.track_plot = pg.PlotItem()
		self.track_view = pg.ImageView(view=self.track_plot)
		self.track_view.ui.roiBtn.hide()
		try:
			self.track_view.ui.menuBtn.hide()
		except:
			self.track_view.ui.normBtn.hide()
		self.view = self.track_plot.getViewBox()
		self.freehand = FreehandROI(self.view, 0, 0)
		self.view.mouseDragEvent=self.mouseDragEvent
		self.track_plot.scene().sigMouseMoved.connect(self.mouseMoved)
		self.view.mouseClickEvent=self.mouseClickEvent
		self.image_item = self.track_view.getImageItem()
		self.image = np.zeros((2, 2))
		self.options_box = OptionsWidget('Exclude Tracks Outside Specifications', \
					[{'key': 'min_mean_mld', 'name': 'Mean Distance Per Lag Minimum(px)', 'value':0.0, 'bounds':(0.0, 10.0)},\
					 {'key': 'max_mean_mld', 'name': 'Mean Distance Per Lag Maximum(px)', 'value':5.0, 'bounds':(0.0, 10.0)},\
					 {'key': 'neighbors', 'name': 'Neighbors Required: ', 'value': 0.0},\
					 {'key': 'epsilon', 'name': 'Neighborly Distance(px)', 'value': 5.0, 'bounds': (0.0, None)}])
		self.options_box.setHidden(True)
		self.options_box.valueChanged.connect(self.update)

		self.show_tracks_check = QCheckBox("Show Track Paths")
		self.show_tracks_check.nextCheckState()
		self.show_tracks_check.stateChanged.connect(lambda f: self.toggle_plotitem(f, self.all_tracks_plot))

		self.show_points_check = QCheckBox("Show Track XY Points")
		self.show_points_check.stateChanged.connect(lambda f: self.toggle_plotitem(f, self.all_points_plot))

		self.show_means_check = QCheckBox("Show Track Mean XYs")
		self.show_means_check.stateChanged.connect(lambda f: self.toggle_plotitem(f, self.all_means_plot))

		self.background_check = QCheckBox("Show Background Image")
		self.background_check.nextCheckState()
		self.background_check.stateChanged.connect(self.toggle_background)


		self.legend = pg.LegendItem()
		self.legend.setParentItem(self.track_plot)

		self.xys = {}
		self.symbols = ['o', 't', '+']

		open_tracks_button = QPushButton("Import .bin File")
		open_tracks_button.clicked.connect(self.openSignal.emit)
		import_background_button = QPushButton("Import Background Image")
		import_background_button.clicked.connect(self.import_background)
		import_locations_button = QPushButton("Import FLIKA XY Locations")
		import_locations_button.clicked.connect(self.import_locations)
		import_means_button = QPushButton("Import FLIKA Mean XYs")
		import_means_button.clicked.connect(lambda : self.import_locations(means=True))

		self.exclude_tracks_check = QCheckBox('Show Outlined Tracks Only')
		self.exclude_tracks_check.stateChanged.connect(lambda : self.update())

		show_options = QCheckBox("Show Options")
		show_options.clicked.connect(self.toggle_options)

		self.addWidget(self.track_view, 0, 0, 4, 5)
		self.addWidget(self.show_tracks_check, 4, 0)
		self.addWidget(self.show_points_check, 5, 0)
		self.addWidget(self.show_means_check, 6, 0)
		self.addWidget(open_tracks_button, 4, 1)
		self.addWidget(self.exclude_tracks_check, 4, 2)
		self.addWidget(import_background_button, 5, 1)
		self.addWidget(self.background_check, 5, 2)
		self.addWidget(import_locations_button, 6, 1)
		self.addWidget(import_means_button, 6, 2)
		self.addWidget(show_options, 7, 0)
		self.addWidget(self.options_box, 8, 0, 1, 5)

		pg.setConfigOptions(antialias=True)

	def toggle_options(self, val):
		self.options_box.setHidden(not val)

	def save_outlined_tracks(self):
		self.add_process('Saving Outlined Tracks')
		filename = getSaveFileName(caption='Save tracks to an excel file...', filter="Text Files (*.txt)", info="tracks")
		if filename == '':
			return
		outFile = open(filename, 'w')
		line = 1
		outFile.write('X\tY\n')
		tracks = self.exclude_tracks()
		for i, track in enumerate(tracks):
			for i in range(1, len(track['x'])):
				outFile.write("%s\t%s\n" % (track['x'][i], track['y'][i]))
			outFile.write('\n')

		outFile.close()
		self.remove_process('Saving Outlined Tracks')

	def apply_to_tracks(self, func, track_list=[]):
		if not self.loaded:
			return
		if track_list == []:
			track_list = self.all_tracks
		to_return = [tr for tr in track_list if func(tr)]
		return to_return

	def get_tracks_in_rois(self, track_list=[]):
		if len(self.rois) == 0:
			return self.all_tracks
		if track_list == []:
			track_list = self.all_tracks
		return self.apply_to_tracks(lambda tr: any([roi.contains(tr['xmean'], tr['ymean']) for roi in self.rois]), track_list=track_list)

	def import_background(self):
		filename = getFileName(caption='Select an image for a transparent background')
		if not os.path.isfile(filename):
			return
		self.to = TiffOpener(filename)
		self.to.Image_Loaded_Signal.connect(lambda : self.toggle_background(img = self.to.tif))
		self.background_check.setCheckState(2)
		try:
			self.add_process("Importing Background")
			self.to.start()
		except:
			print("Not a tif file, cannot load")
			return

	def toggle_background(self, val = True, img = []):
		self.remove_process("Importing Background")
		self.add_process("Loading Background")
		if np.array(img).size > 0:
			self.image = img

		if not val:
			self.track_view.setImage(np.zeros((2, 2)), autoLevels=False)
		else:
			self.track_view.setImage(self.image)
		self.remove_process("Loading Background")
		self.update()

	def add_process(self, process):
		assert type(process) == str, "Musty provide process as a string"
		self.background_processes.append(process)
		self.updateStatusBar()

	def remove_process(self, process):
		if process not in self.background_processes:
			return
		self.background_processes.remove(process)
		self.updateStatusBar()

	def save_xy_mean_differences(self, name):
		to_map = np.array([(tr['xmean'], tr['ymean']) for tr in self.exclude_tracks()])
		map_to = np.array([xy for xy in zip(*self.xys[name]['scatter'].getData())])
		self.dms = DistanceMapSaver(to_map, map_to, info='flika_mean_distances')
		self.dms.DoneSignal.connect(lambda : self.remove_process("Saving Mapped Distances"))
		if self.dms.filename != "":
			self.add_process("Saving Mapped Distances")
			self.dms.start()
		else:
			del self.dms

	def save_distances(self):
		if not hasattr(self, "all_means_plot"):
			raise Exception("No data has been loaded yet")
		maxDist = float(QInputDialog.getInt(self, "Enter the maximum distance in pixels", "Maximum distance in pixels (0 for None)", 2)[0])
		if maxDist == 0:
			maxDist = None
		self.ds = DistanceSaver(self.all_means_plot.getData(), maxDist=maxDist, info='distances')
		self.ds.DoneSignal.connect(lambda : self.remove_process("Saving Distances"))
		if self.ds.filename != "":
			self.add_process("Saving Distances")
			self.ds.start()
		else:
			del self.ds

	def save_plotted(self):
		filename = getSaveFileName(caption='Save plotted points to text file...', info="data", filter="Text Files (*.txt)")
		if filename == '':
			return
		means = self.show_means_check.isChecked()
		points = self.show_points_check.isChecked()
		if not (points or means):
			print("Nothing to export")
			return
		self.add_process('Saving Plotted Data')
		mean_data = self.all_means_plot.getData()
		pt_data = self.all_points_plot.getData()
		with open(filename, 'w') as out_file:
			line = ("%s\t%s" % ("MeanX", "MeanY")) if means else ""
			if points:
				line = "%s\t%s\t%s" % (line, 'TrackXs', 'TrackYs')
			line += "\n"
			out_file.write(line)
			for i in range(max([len(mean_data[0]), len(pt_data[0])])):
				line = ''
				if means:
					line += "%.3f\t%.3f" % ((mean_data[0][i], mean_data[1][i]) if i < len(mean_data[0]) else (-1, -1))
					if points:
						line += "\t"
				if points:
					line += "%.3f\t%.3f" % ((pt_data[0][i], pt_data[1][i]) if i < len(pt_data[0]) else (-1, -1))
				out_file.write(line + "\n")
		self.remove_process('Saving Plotted Data')

	def import_locations(self, means=False):
		self.add_process('Importing FLIKA')
		filename = getFileName(caption='Select an excel file with xy columns in "Puff Data" sheet of workbook...', filter="Excel Files (*.xls)")
		if not os.path.isfile(filename):
			return
		locs = read_locations(filename, columns={'Group x' if means else 'x': 'x', 'Group y' if means else 'y': 'y'})
		x, y = locs['x'], locs['y']
		def remove_scatter(name):
			self.symbols.insert(0, self.xys[name]['symbol'])
			self.track_plot.removeItem(self.xys[name]['scatter'])
			self.xys[name]['button'].deleteLater()
			self.xys[name]['save'].deleteLater()
			self.legend.removeItem(os.path.basename(name))
			del self.xys[name]
		name = os.path.basename(filename)
		pen = QColor(255, 255, 0)
		if means:
			filename += '(means)'
			name += '(means)'
			pen = QColor(255, 125, 0)
		if filename in self.xys:
			return
		self.xys[filename] = {'pos': np.array(zip(x,y)), 'scatter': pg.ScatterPlotItem(pos=np.array(zip(x,y)), symbol=self.symbols[0], brush=pen, pen=pen, size=5), \
							'button': QPushButton('Remove...'), 'symbol': self.symbols[0], 'brush': pen, \
							'save' : QPushButton('Save Track Mean XY to FlIKA XYs for %s' % name)}
		self.track_plot.addItem(self.xys[filename]['scatter'])
		self.legend.addItem(self.xys[filename]['scatter'], name=name)
		self.addWidget(self.xys[filename]['button'], 4+3-len(self.symbols), 4)
		self.addWidget(self.xys[filename]['save'], 4+3-len(self.symbols), 3)
		self.xys[filename]['button'].clicked.connect(lambda : remove_scatter(filename))
		self.xys[filename]['save'].clicked.connect(lambda : self.save_xy_mean_differences(filename))
		self.symbols = self.symbols[1:]
		self.remove_process('Importing FLIKA')

	def toggle_plotitem(self, val, plotitem):
		if not self.loaded:
			return
		if val:
			if plotitem not in self.track_plot.listDataItems():
				self.track_plot.addItem(plotitem)
		else:
			self.track_plot.removeItem(plotitem)

	def get_scatter_count(self):
		c = 0
		for name in self.xys:
			c += len(self.xys[name]['pos'])
		return c

	def get_track_count(self):
		if not hasattr(self, 'all_means_plot'):
			return 0
		return len(self.all_means_plot.getData()[0])

	def set_tracks(self, tracks):
		self.all_tracks = tracks
		for j in range(len(self.all_tracks)):
			tr = self.all_tracks[j]
			self.all_tracks[j]['mean_lag_distance'] = mean([distance((tr['x'][i], tr['y'][i]), (tr['x'][i+1], tr['y'][i+1])) for i in range(len(tr['x']) - 1)])
		self.loaded = True
		self.track_plot.getViewBox().enableAutoRange(axis=pg.ViewBox.XYAxes, enable=True)
		self.update()

	def image_shape(self):
		if self.image.size > 30:
			if self.image.ndim == 2:
				return self.image.shape
			else:
				return self.image.shape[-2], self.image.shape[-1]
		elif hasattr(self, 'all_points_plot'):
			y, x = self.all_points_plot.getData()
			return (max(y) - min(y)), (max(x) - min(x))
		return (250, 250)

	def exclude_tracks(self):
		if len(self.all_tracks) == 0:
			return
		tracks = self.all_tracks
		if len(self.rois) > 0 and self.exclude_tracks_check.isChecked():
			tracks = self.get_tracks_in_rois(track_list=tracks)
			for name in self.xys:
				self.xys[name]['scatter'].setData(pos=[p for p in self.xys[name]['pos'] if any([roi.contains(*p) for roi in self.rois])])
		else:
			for name in self.xys:
				self.xys[name]['scatter'].setData(pos=self.xys[name]['pos'])

		min_mld = self.options_box.get('min_mean_mld')
		max_mld = self.options_box.get('max_mean_mld')
		neighbors = self.options_box.get('neighbors')
		epsilon = self.options_box.get('epsilon')

		#exclude tracks outside mean lag range
		tracks = self.apply_to_tracks(lambda tr: tr['mean_lag_distance'] >= min_mld and tr['mean_lag_distance'] <= max_mld, track_list=tracks)
		#exlcude tracks with neighbors < n within epsilon x
		if neighbors > 0:
			to_return = []
			for tr in sorted(tracks, key=lambda f: f['xmean']):
				x, y = tr['xmean'], tr['ymean']
				if len([t for t in tracks if abs(x - t['xmean']) <= epsilon and distance((t['xmean'], t['ymean']), (x, y)) <= epsilon]) >= neighbors:
					to_return.append(tr)
			tracks = to_return
		return tracks

	def update(self):
		if not self.loaded:
			return
		tracks = self.exclude_tracks()
		if hasattr(self, 'all_tracks_plot') and hasattr(self, 'all_points_plot') and hasattr(self, 'all_means_plot'):
			self.all_tracks_plot.set_tracks(tracks)
			if len(tracks) > 0:
				self.all_points_plot.setData(pos = np.array([(x, y) for tr in tracks for (x, y) in zip(tr['x'], tr['y'])]))
				self.all_means_plot.setData(pos = np.array([(tr['xmean'], tr['ymean']) for tr in tracks]))
			else:
				self.all_points_plot.clear()
				self.all_means_plot.clear()
		else:
			self.all_tracks_plot = TrackGraphItem(tracks)
			self.all_points_plot = pg.ScatterPlotItem(pos = np.array([(x, y) for tr in tracks for (x, y) in zip(tr['x'], tr['y'])]), symbol='o', pen='m', size=3)
			self.all_means_plot = pg.ScatterPlotItem(pos = np.array([(tr['xmean'], tr['ymean']) for tr in tracks]), symbol='x', pen='r', size=5)
			self.legend.addItem(self.all_points_plot, name='Track Path XYs')
			self.legend.addItem(self.all_means_plot, name='Track Mean XYs')
			self.track_plot.addItem(self.all_tracks_plot)
			#self.addPlots()
		self.track_plot.getViewBox().enableAutoRange(axis=pg.ViewBox.XYAxes, enable=False)
		self.updateStatusBar()
		self.tracksChanged.emit()

	def mouseMoved(self,point):
		point=self.image_item.mapFromScene(point)
		self.x=point.x()
		self.y=point.y()
		for roi in self.rois:
			roi.mouseOver(self.x, self.y)
			if self.creatingROI is False:
				if roi.contains(self.x,self.y):
					self.currentROI=roi
		self.updateStatusBar()

	def updateStatusBar(self):
		x = -1 if type(self.x) not in (int, float) else self.x
		y = -1 if type(self.y) not in (int, float) else self.y
		tracks = self.get_track_count()
		if type(tracks) not in (int, float):
			tracks = 0
		scatters = self.get_scatter_count()
		if type(scatters) not in (int, float):
			scatters = 0
		message = "Mouse at (%.2f, %.2f), %d tracks shown, %d FLIKA points mapped" % (x, y, tracks, scatters)
		if len(self.background_processes) > 0:
			message += "\t    %s" % ("Processes[%s]" % ",".join(self.background_processes))
		self.status.showMessage(message)

	def mouseClickEvent(self,ev):
		if self.x is not None and self.y is not None and ev.button()==2:
			if self.creatingROI is False:
				if self.currentROI is not None and self.currentROI.contains(self.x,self.y):
					self.currentROI.contextMenuEvent(ev)
					self.x=None
					self.y=None
					ev.accept()
					return

	def erase_in_currentROI(self):
		self.set_tracks(self.apply_to_tracks(lambda tr: all([not roi.contains(tr['xmean'], tr['ymean']) for roi in self.rois])))

	def delete_currentROI(self):
		if self.currentROI in self.rois:
			self.rois.remove(self.currentROI)
		if self.exclude_tracks_check.isChecked():
			self.update()
		self.currentROI = None

	def mouseDragEvent(self, ev):
		if ev.button() == Qt.LeftButton:
			ev.accept()
			difference=self.image_item.mapFromScene(ev.lastScenePos())-self.image_item.mapFromScene(ev.scenePos())
			self.view.translateBy(difference)
		if ev.button() == Qt.RightButton:
			ev.accept()
			if ev.isStart():
				self.ev=ev
				pt=self.image_item.mapFromScene(ev.buttonDownScenePos())
				self.x=pt.x() # this sets x and y to the button down position, not the current position
				self.y=pt.y()
				#print("Drag start x={},y={}".format(self.x,self.y))
				for roi in self.rois:
					roi.mouseOver(self.x,self.y)
				if any([roi.mouseIsOver for roi in self.rois]): #if any roi is moused over
					self.creatingROI=False
				else:
					self.creatingROI=True
					self.currentROI=FreehandROI(self.view,self.x,self.y)
					self.currentROI.deleteSignal.connect(self.delete_currentROI)
					self.currentROI.translated.connect(lambda : self.update() if self.exclude_tracks_check.isChecked() else None)
					self.currentROI.eraseInsideSignal.connect(self.erase_in_currentROI)
			if ev.isFinish():
				if self.creatingROI:
					self.add_process("Creating ROI")
					self.currentROI.drawFinished()
					self.creatingROI=False
					if self.currentROI != None:
						self.rois.append(self.currentROI)
					self.currentROI = None
					self.update()
					self.remove_process("Creating ROI")
				else:
					for roi in self.currentROIs:
						roi.finish_translate()
			else: # if we are in the middle of the drag between starting and finishing
				#if inImage:
				if self.creatingROI:
					self.currentROI.extend(self.x,self.y)
				else:
					difference=self.image_item.mapFromScene(ev.scenePos())-self.image_item.mapFromScene(ev.lastScenePos())
					if difference.isNull():
						return
					self.currentROI.translate(difference,self.image_item.mapFromScene(ev.lastScenePos()))

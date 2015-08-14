"""
@author: Brett Settle
@Department: UCI Neurobiology and Behavioral Science
@Lab: Parker Lab
@Date: August 6, 2015
"""
from pyqtgraph.dockarea import *
from TrackBasics import *

class RandomDistancePlot(Dock):
	def __init__(self, parent, *args, **kargs):
		shape = (0, 0)
		if 'shape' in kargs:
			shape = kargs['shape']
			del kargs['shape']
		self.parent = parent
		super(RandomDistancePlot, self).__init__(*args, **kargs)
		self.plot = pg.PlotWidget(title='Simulated Data Points')
		self.legend = pg.LegendItem()
		self.legend.setParent(self.plot.getPlotItem())
		self.plot.showGrid(x=True, y=True, alpha=.5)
		self.track_item = pg.ScatterPlotItem()
		self.plot.addItem(self.track_item)
		self.legend.addItem(self.track_item, name='Track Mean XY')
		self.flika_item = pg.ScatterPlotItem()
		self.plot.addItem(self.flika_item)
		self.legend.addItem(self.flika_item, name='Puff Mean XY')
		self.track_mean_spin = pg.SpinBox(value=0)
		self.flika_mean_spin = pg.SpinBox(value=0)
		self.width_spin = pg.SpinBox(value=shape[0])
		self.height_spin = pg.SpinBox(value=shape[1])
		generateBtn = QPushButton('Generate Random Points')
		generateBtn.clicked.connect(self.generate)
		exportDistancesBtn = QPushButton('Export All Distances')
		exportDistancesBtn.clicked.connect(self.export_all_distances)
		saveBtn = QPushButton('Save Track-Flika Distances')
		saveBtn.clicked.connect(self.save_distances)
		closeBtn = QPushButton('Close Dock')
		closeBtn.clicked.connect(lambda : self.parent.remove_dock(self))

		self.addWidget(self.plot, 0, 0, 4, 4)
		self.addWidget(QLabel('Track Mean XY Count:'), 4, 0)
		self.addWidget(self.track_mean_spin, 4, 1)
		self.addWidget(QLabel('FLIKA Mean XY Count:'), 5, 0)
		self.addWidget(self.flika_mean_spin, 5, 1)
		self.addWidget(QLabel('Maximum X:'), 4, 2)
		self.addWidget(self.width_spin, 4, 3)
		self.addWidget(QLabel('Maximum Y:'), 5, 2)
		self.addWidget(self.height_spin, 5, 3)
		self.addWidget(closeBtn, 6, 0)
		self.addWidget(exportDistancesBtn, 6, 1)
		self.addWidget(saveBtn, 6, 2)
		self.addWidget(generateBtn, 6, 3)

        def export_all_distances(self):
		maxDist = float(QInputDialog.getInt(self, "Enter the maximum distance in pixels", "Maximum distance in pixels (0 for None)", 2)[0])
		if maxDist == 0:
			maxDist = None
		self.ds = DistanceSaver(self.track_item.getData(), maxDist=maxDist, info='random_distances')
		if self.ds.filename != "":
                        self.ds.start()
		else:
			del self.ds


	def save_distances(self):
		self.dms = DistanceMapSaver(zip(*self.track_item.getData()), zip(*self.flika_item.getData()), info='random_flika_mean_distances')
		self.dms.start()

	def generate(self):
		tracks = self.track_mean_spin.value()
		puffs = self.flika_mean_spin.value()
		h = self.height_spin.value()
		w = self.width_spin.value()
		self.track_item.setData(x=np.random.random(tracks) * w, y = np.random.random(tracks) * h, pxMode=True, pen='r', symbol='x', name = 'Track Mean XY')
		self.flika_item.setData(x=np.random.random(puffs) * w, y = np.random.random(puffs) * h, pen='y', pxMode=True, symbol='d', name = 'FLIKA Mean XY')
		self.plot.getPlotItem().autoRange()

	def set_track_count(self, v):
		self.track_mean_spin.setValue(v)

	def set_flika_count(self, v):
		self.flika_mean_spin.setValue(v)

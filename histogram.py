import pyqtgraph as pg
import numpy as np
from PyQt4 import QtCore, QtGui
from process.BaseProcess import BaseDialog, SliderLabel
import global_vars as g

class Histogram(pg.PlotWidget):
	def __init__(self, *args, **kwargs):
		super(Histogram, self).__init__(*args, **kwargs)
		self.plotitem = pg.PlotDataItem()
		self.addItem(self.plotitem)
		self.bins = np.zeros(1)
		self.n_bins = 0
		self.minimum = 0.
		self.maximum = 0.
		self.plot_data = []

	def setData(self, data=[], n_bins=None):
		if n_bins is None:
			n_bins = data.size ** 0.5
		if len(data) == 0:
			data = self.plot_data

		minimum = np.min(data)
		maximum = np.max(data)

		# if this is the first histogram plotted,
		# initialize_c settings
		self.minimum = minimum
		self.maximum = maximum
		self.n_bins = n_bins
		self.bins = np.linspace(self.minimum, self.maximum, int(self.n_bins + 1))

		# re-plot the other histograms with this new
		# binning if needed
		re_hist = False
		if minimum < self.minimum:
			self.minimum = minimum
			re_hist = True
		if maximum > self.maximum:
			self.maximum = maximum
			re_hist = True
		if n_bins > self.n_bins:
			self.n_bins = n_bins
			re_hist = True

		if re_hist:
			self.reset()

		self._plot_histogram(data)

	def preview(self, n_bins=None):
		if n_bins == None:
			n_bins = len(self.plotitem.getData()[1])

		bins = np.linspace(np.min(self.plot_data), np.max(self.plot_data), int(n_bins + 1))
		y, x = np.histogram(self.plot_data, bins=bins)
		self.plotitem.setData(x=x, y=y, stepMode=True, fillLevel=0)

	def _plot_histogram(self, data):

		# Copy self.bins, otherwise it is returned as x, which we can accidentally modify
		# by x *= -1, leaving self.bins modified.
		bins = self.bins.copy()
		y, x = np.histogram(data, bins=bins)

		self.plotitem.setData(x=x, y=y, stepMode=True, fillLevel=0)

		self.plot_data = data

	def reset(self):
		self.bins = np.linspace(self.minimum, self.maximum, self.n_bins + 1)
		bins = self.bins.copy()
		y, x = np.histogram(self.plot_data, bins=bins)

		self.plotitem.setData(x, y)

	def mouseDoubleClickEvent(self, ev):
		ev.accept()
		super(Histogram, self).mouseDoubleClickEvent(ev)
		if len(self.plot_data) > 0:
			edit_histogram_gui(self)

	def export(self, filename):
		np.savetxt(filename, self.plot_data, header='Mean Single Lag Distances')

def edit_histogram_gui(hist):
	items = []
	binSlider = SliderLabel(0)
	binSlider.setMinimum(1)
	binSlider.setMaximum(len(hist.plot_data))
	binSlider.setValue(hist.n_bins)
	items.append({'name': 'Bins', 'string': 'Bins', 'object': binSlider})
	bd = BaseDialog(items, "Histogram options", 'Set the number of bins in the histogram')
	bd.accepted.connect(lambda : hist.setData(n_bins=binSlider.value()))
	bd.rejected.connect(hist.reset)
	bd.changeSignal.connect(lambda : hist.preview(n_bins=binSlider.value()))
	bd.show()
	g.m.dialog = bd
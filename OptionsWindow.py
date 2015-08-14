"""
@author: Brett Settle
@Department: UCI Neurobiology and Behavioral Science
@Lab: Parker Lab
@Date: August 6, 2015
"""
import pyqtgraph as pg
from PyQt4.QtCore import *
from PyQt4.QtGui import *
import numpy as np
import pyqtgraph.parametertree.parameterTypes as pTypes
from pyqtgraph.parametertree import Parameter, ParameterTree, ParameterItem, registerParameterType

class OptionsWidget(QGroupBox):
	valueChanged = Signal()
	def __init__(self, title, options):
		super(OptionsWidget, self).__init__(title=title)
		self.pos = (0, 0)
		count = len(options * 2)
		self.shape = np.ceil(count / 6.), 6
		self.layout = QGridLayout(self)
		self.options = {}
		for var_dict in options:
			self.build_option(var_dict)

	def increment_pos(self):
		self.pos = [self.pos[0], self.pos[1] + 1]
		if self.pos[1] >= self.shape[1]:
			self.pos[1] = 0
			self.pos[0] += 1

	def get(self, name):
		if name in self.options:
			return self.options[name]
		return None

	def update_value(self, name, value):
		self.options[name] = value
		self.valueChanged.emit()

	def build_option(self, var_dict):
		try:
			key = var_dict['key']
			value = var_dict['value']
			name = var_dict['name']
			del var_dict['key'], var_dict['name'], var_dict['value']
		except:
			return
		self.options[key] = value
		self.layout.addWidget(QLabel(name + ": "), self.pos[0], self.pos[1])
		self.increment_pos()
		if type(value) in (int, float):
			new_widget = pg.SpinBox(value=value, **var_dict)
		else:
			new_widget = QTextEdit(text=str(value), **var_dict)
		new_widget.valueChanged.connect(lambda f : self.update_value(key, f))
		self.layout.addWidget(new_widget, self.pos[0], self.pos[1])
		self.increment_pos()
class ScalableGroup(pTypes.GroupParameter):
	'''Group used for entering and adding parameters to ParameterWidget'''
	def __init__(self, **opts):
		opts['type'] = 'group'
		opts['addText'] = "Add"
		opts['addList'] = ['str', 'float', 'int', 'color']
		pTypes.GroupParameter.__init__(self, **opts)

	def addNew(self, typ):
		val = {
			'str': '',
			'float': 0.0,
			'int': 0,
			'color': (255, 255, 255)
		}[typ]
		self.addChild(dict(name="New Parameter %d" % (len(self.childs)+1), type=typ, value=val, removable=True, renamable=True))

	def getItems(self):
		items = {}
		for k, v in self.names.items():
			if isinstance(v, ScalableGroup):
				items[k] = v.getItems()
			else:
				items[k] = v.value()
		return items

class ParameterWidget(QWidget):
	'''Widget used to enter information and then closed with a button'''
	done = Signal(dict)
	valueChanged = Signal(dict)
	def __init__(self, title, paramlist, about=""):
		super(ParameterWidget, self).__init__()
		self.parameters = ScalableGroup(name="Parameters", children=ParameterWidget.build_parameter_list(paramlist))
		self.parameters.sigTreeStateChanged.connect(self.paramsChanged)
		self.info = about
		self.key_dict = {p['name']: (p['key'] if 'key' in p else p['name']) for p in paramlist}
		self.tree = ParameterTree()
		self.tree.setParameters(self.parameters, showTop=False)
		self.tree.setWindowTitle(title)
		self.makeLayout()
		self.resize(800,400)

	@staticmethod
	def type_as_str(var):
		if isinstance(var, QColor):
			return 'color'
		if isinstance(var, dict) or (isinstance(var, list) and all([type(i) == dict for i in var])):
			return 'group'
		elif isinstance(var, bool):
			return 'bool'
		elif isinstance(var, (float, long)):
			return 'float'
		elif isinstance(var, int):
			return 'int'
		elif isinstance(var, str):
			return 'str'
		elif isinstance(var, (list, tuple)):
			return 'list'
		elif isinstance(var, QPushButton):
			return 'action'
		else:
			return 'text'

	def paramsChanged(self, params):
		to_emit = {}
		for child in params.childs:
			n, v = child.name(), child.value()
			if n not in self.key_dict:
				self.key_dict[n] = n
			if isinstance(v, (QString, unicode)):
				to_emit[self.key_dict[n]] = str(v)
			else:
				to_emit[self.key_dict[n]] = v
		self.valueChanged.emit(to_emit)

	def makeLayout(self):
		layout = QGridLayout()
		cancelButton = QPushButton("Cancel")
		cancelButton.clicked.connect(lambda : self.doneClick(save=False))
		okButton = QPushButton("Ok")
		okButton.clicked.connect(lambda : self.doneClick(save=True))
		self.setLayout(layout)
		self.scrollArea = QScrollArea(self)
		self.scrollArea.setWidgetResizable(True)
		self.scrollArea.setWidget(QLabel(self.info))
		layout.addWidget(self.scrollArea, 0,  0, 1, 2)
		layout.addWidget(self.tree, 1, 0, 3, 2)
		layout.addWidget(cancelButton, 4, 0)
		layout.addWidget(okButton, 4, 1)

	@staticmethod
	def build_parameter_list(params):
		return_params = []
		for param_dict in params:
			assert 'name' in param_dict, 'Must provide a name for each item'
			if 'type' not in param_dict:
				v = {'value', 'values', 'action', 'children'} & set(param_dict.keys())
				assert len(v) == 1, 'Must give a value, list of values, or action if no type is given for %s' % param_dict['name']
				param_dict['type'] = ParameterWidget.type_as_str(param_dict[list(v)[0]])
			if param_dict['type'] == 'group':
				return_params.append(ScalableGroup(name=param_dict['name'], children=ParameterWidget.build_parameter_list(param_dict['children'])))
			else:
				if 'removable' not in param_dict:
					param_dict['removable'] = True
				if 'renamable' not in param_dict:
					param_dict['renamable'] = False
				if param_dict['type'] == 'color': # takes colors in as QColor, shows them as "FFF"
					param_dict['value'] = str(param_dict['value'].name())
				return_params.append(param_dict)
		return return_params

	def doneClick(self, save=False):
		self.close()
		if save == True:
			self.params = {self.key_dict[k]: v for k, v in self.parameters.getItems().items() if not isinstance(v, QPushButton)}
			self.done.emit(self.params)

if __name__ == '__main__':
	app = QtGui.QApplication([])
	import sys
	if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
		QtGui.QApplication.instance().exec_()

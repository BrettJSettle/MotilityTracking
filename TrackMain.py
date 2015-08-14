"""
@author: Brett Settle
@Department: UCI Neurobiology and Behavioral Science
@Lab: Parker Lab
@Date: August 6, 2015
"""
from TrackBasics import *
from TracksDock import TracksDock
from MSD_plot import *
from pyqtgraph.dockarea import *
from bin2mat import bin2mat
from RandomDistancePlot import RandomDistancePlot
from CDF_Widget import CDFWidget, calculate_cdfs
from OptionsWindow import ParameterWidget

class MainWindow(QMainWindow):
    def __init__(self):
        app = QApplication([])
        super(MainWindow, self).__init__()
        self.resize(1000,800)
        self.files = []

        self.da = DockArea("Tracking")
        self.setCentralWidget(self.da)
        self.tracks_dock = TracksDock(self, "Dock1 - Tracks", size=(300,300))
        self.tracks_dock.openSignal.connect(self.openFile)
        self.msd_dock = MSDDock("Dock2 - MSD Plot", size=(400, 400))
        self.msd_dock.Range_Changed_Signal.connect(self.range_changed)
        self.da.addDock(self.msd_dock)
        self.da.addDock(self.tracks_dock, 'below', self.msd_dock)
        self.tracks_dock.tracksChanged.connect(lambda : self.load_plots(with_global=False))
        self.make_menus()
        self.random_docks = []

        self.show()
        app.exec_()

    def make_menus(self):
        menuBar = self.menuBar()
        fileMenu = menuBar.addMenu('&File')
        openAction = fileMenu.addAction(QAction('&Open .bin file(s)', fileMenu, triggered=self.openFile))
        addAction = fileMenu.addAction(QAction('&Add .bin file(s)', fileMenu, triggered=lambda : self.openFile(add=True)))
        importMenu = menuBar.addMenu('&Import')
        importBackgroundAction = importMenu.addAction(QAction('Import &Background Image', importMenu, triggered=self.tracks_dock.import_background))
        importXYAction = importMenu.addAction(QAction('Import FLIKA &XYs', importMenu, triggered=self.tracks_dock.import_locations))
        importMeanXYAction = importMenu.addAction(QAction('Import FLIKA &Mean XYs', importMenu, triggered=lambda: self.tracks_dock.import_locations(means=True)))
        self.generateMenu = menuBar.addMenu('&Generate')
        generateRandAction = self.generateMenu.addAction(QAction('Generate &Random Simulation', self.generateMenu, triggered=self.add_random_dock))
        generateCDFAction = self.generateMenu.addAction(QAction('Generate &CDF Graph', self.generateMenu, triggered=self.add_cdf_dock))
        exportMenu = menuBar.addMenu('&Export')
        exportMSDAction = exportMenu.addAction(QAction('Export &MSD Values', exportMenu, triggered=self.msd_dock.export_msd))
        exportHistAction = exportMenu.addAction(QAction('Export &Histogram Values', exportMenu, triggered=self.msd_dock.export_hist))
        exportOutlinedAction = exportMenu.addAction(QAction('Export &Outlined Tracks', exportMenu, triggered=self.tracks_dock.save_outlined_tracks))
        exportDistancesAction = exportMenu.addAction(QAction('Export All Distances', exportMenu, triggered=self.tracks_dock.save_distances))
        exportPlottedAction = exportMenu.addAction(QAction('Export Plotted Data', exportMenu, triggered=self.tracks_dock.save_plotted))

    def add_random_dock(self):
        num = len(self.random_docks)
        new_dock = RandomDistancePlot(self, 'Random Data %s' % (num + 1), size=(400, 400), shape=self.tracks_dock.image_shape())
        new_dock.set_track_count(self.tracks_dock.get_track_count())
        new_dock.set_flika_count(self.tracks_dock.get_scatter_count())
        self.random_docks.append(new_dock)
        self.da.addDock(self.random_docks[-1], 'above', self.tracks_dock)
        self.random_docks[-1].generate()

    def add_cdf_dock(self):
        par_det, _, _ = create_main_data_struct(global_tracks, ltl, utl)
        cdfs = calculate_cdfs(par_det)
        if hasattr(self, "cdf_widget"):
            self.cdf_widget.update(cdfs)
            return
        num = len(self.random_docks)
        cdf_widget = CDFWidget(cdfs)
        new_dock = Dock('CDF %s' % (num + 1), size=(400, 400))
        new_dock.addWidget(cdf_widget)
        self.random_docks.append(new_dock)
        self.da.addDock(new_dock, 'above', self.tracks_dock)

    def remove_dock(self, dock):
        dock.close()
        self.random_docks.remove(dock)

    def openFile(self, add=False):
        global global_tracks
        if add == False:
            self.files = []
            global_tracks = []
        fs = getFileName(multiple=True, filter='Bin Files (*.bin)')
        for f in fs:
            if f not in self.files:
                self.files.append(f)
                global_tracks.extend(bin2mat(f))
        if global_tracks == []:
            return


        self.pw = ParameterWidget('Correct for blinking?', [{'name': 'Correct Blinking', 'value': False},\
            {'name': 'Temporal Dilation (frames)', 'value': 25}, {'name': 'Spatial Dilation (px)', 'value': 1}], \
            "Set parameters for blink correction in tracking motility.")
        self.pw.done.connect(lambda p: self.load_plots(blink_args=(p['Temporal Dilation (frames)'], p['Spatial Dilation (px)']) if p['Correct Blinking'] else []))
        self.pw.show()

    def range_changed(self):
        tracks = [tr for tr in global_tracks if len(tr['x']) >= self.msd_dock.low and len(tr['x']) <= self.msd_dock.high]
        self.tracks_dock.set_tracks(tracks)

    def load_plots(self, with_global = True, blink_args=[]):
        if len(blink_args) == 2:
            global global_tracks
            global_tracks = correct_blinking(global_tracks, *blink_args)
        par_det, _, _ = create_main_data_struct((global_tracks if with_global else self.tracks_dock.exclude_tracks()), ltl, utl)
        if with_global:
            self.tracks_dock.set_tracks(global_tracks)
        self.setWindowTitle(", ".join([os.path.basename(s) for s in self.files]))
        self.msd_dock.update(par_det)

if __name__ == "__main__":
    main = MainWindow()

"""
@author: Brett Settle
@Department: UCI Neurobiology and Behavioral Science
@Lab: Parker Lab
@Date: August 6, 2015
"""
from pyqtgraph.dockarea import *
from TrackBasics import *

max_lag=20

class MSDDock(Dock):
    Range_Changed_Signal = Signal()
    def __init__(self, *args, **kargs):
        self.loaded = False
        super(MSDDock, self).__init__(*args, **kargs)

        self.msd_data = {'x': [], 'y': [], 'er':[]}
        self.hist_data = {'x': [], 'y':[]}

        self.msd_plot = pg.PlotWidget(title="Mean Squared Distance")
        self.msd_plot.setLabel('left', text='Distance Squared (Pixels^2)')
        self.msd_plot.setLabel('bottom', text='Lags')

        self.lowMSD = pg.SpinBox(value=1, int=True, step=1)
        self.lowMSD.sigValueChanged.connect(self.range_changed)
        self.highMSD = pg.SpinBox(value=max_lag, int=True, step=1)
        self.highMSD.sigValueChanged.connect(self.range_changed)
        MSDlabel = QLabel(" > Track Length >= ")

        self.histogram = pg.PlotWidget(title='Mean Lag Distance Counts')
        self.histogram.setLabel('left', text='Count')
        self.histogram.setLabel('bottom', text='Mean SLD Per Track (Pixels)')

        self.binsize = 40
        self.binspin = pg.SpinBox(value=self.binsize, step=1)
        self.binspin.sigValueChanged.connect(self.update_histogram)
        binlabel = QLabel("Bin count: ")
        binlabel.setAlignment(Qt.AlignRight)
        self.addWidget(binlabel, 10, 0, 1, 2)
        self.addWidget(self.binspin, 10, 2, 1, 2)

        self.addWidget(self.msd_plot, 0, 0, 4, 4)   # main MSD plot
        self.addWidget(self.lowMSD, 4, 0)   # lower value in mid left
        self.addWidget(MSDlabel, 4, 1)   # range label
        self.addWidget(self.highMSD, 4, 2)  # upper value in the mid right
        self.addWidget(self.histogram, 5, 0, 4, 4)
        self.low = 1
        self.high = max_lag

    def range_changed(self):
        if not self.loaded:
            return
        self.low = int(self.lowMSD.value())
        self.high = int(self.highMSD.value())
        self.Range_Changed_Signal.emit()
        self.update_histogram()
        self.update_msd()

    def update(self, par_det=[]):
        if par_det != []:
            self.par_det = par_det
            self.loaded=True
            self.update_msd()
            self.update_histogram()

    def update_histogram(self):
        if "par_det" not in self.__dict__:
            return
        self.binsize = self.binspin.value()
        self.histogram.clear()
        mean_dists = [tr.mean_dis_pixel_lag for tr in self.par_det if self.low < tr.fr_length <= self.high]
        y, x = np.histogram(mean_dists, self.binsize)
        self.hist_data['x'] = x
        self.hist_data['y'] = y
        self.curve = pg.PlotCurveItem(x, y, stepMode=True, fillLevel=0, brush=(0, 0, 255))
        self.histogram.addItem(self.curve)

    def update_msd(self):
        x, y, er = calculate_MSD_plot(self.par_det, [self.low, self.high])
        self.msd_plot.clear()
        err = pg.ErrorBarItem(x=x, y=y, top=er, bottom=er, beam=0.5)
        self.msd_data['er'] = er
        self.msd_data['x'] = x
        self.msd_data['y'] = y
        self.msd_plot.addItem(err)
        msd = pg.PlotDataItem(x = x, y = y, pen = (0, 255, 0))
        self.msd_plot.addItem(msd)

    def export_within_range(self):
        lower = self.lowMLD.value()
        higher = self.highMLD.value()
        f = getSaveFileName(filter='Excel file (*.xls)', caption='Save Mean Track Lag Distance in [%s, %s] to...' % (lower, higher))
        if f == "":
            return
        workbook = xlwt.Workbook()
        sh = workbook.add_sheet("Track Centers")
        sh.write(0, 0, 'Mean X')
        sh.write(0, 1, 'Mean Y')
        sh.write(0, 2, 'Mean Lag Distance')
        trs = [track for track in self.par_det if lower <= track.mean_dis_pixel_lag <= higher]
        for i, tr in enumerate(sorted(trs, key=lambda f: f.mean_dis_pixel_lag)):
            sh.write(i+1, 0, tr.mean_x)
            sh.write(i+1, 1, tr.mean_y)
            sh.write(i+1, 2, tr.mean_dis_pixel_lag)
        workbook.save(f)

    def export_msd(self):
        f = getSaveFileName(info='MSD', filter='Excel file (*.xls)', caption="Save Mean Squared Distance Export to...")
        if f == "":
            return
        workbook = xlwt.Workbook()
        sh = workbook.add_sheet("MSD Data")
        for i, k in enumerate(('x', 'y', 'er')):
            sh.write(0, i, k)
            for j in range(len(self.msd_data[k])):
                sh.write(j+1, i, self.msd_data[k][j])
        workbook.save(f)

    def export_hist(self):
        f = getSaveFileName(info='histogram', filter='Text file (*.txt)', caption='Save MLDs to...')
        if f == "":
            return
        out = open(f, 'w')
        out.write("Mean Lag Histogram Values\n")
        mean_dists = [tr.mean_dis_pixel_lag for tr in self.par_det if self.low < tr.fr_length <= self.high]
        for d in mean_dists:
            out.write("%s\n" % d)
        out.close()


def calculate_MSD_plot(pcl, lag_range):
    pcl_2 = []
    for i in range(len(pcl)):
        pos_x = pcl[i].x_cor
        pos_y = pcl[i].y_cor

        Nt =np.size(pos_x, 0)-1
        pcl_2.append({})
        pcl_2[i]['max_lag_num'] = Nt
        pcl_2[i]['dist_sqr'] = np.zeros((Nt, Nt))
        pcl_2[i]['mean_dist_sqr'] = np.zeros((Nt))
        for n in range(Nt):
            Na = Nt-n
            sp = 0
            for j in range(Na):
                pcl_2[i]['dist_sqr'][j][n] = (pos_x[sp+n]-pos_x[sp])**2+(pos_y[sp+n]-pos_y[sp])**2
                sp += 1
            proxy_mean = pcl_2[i]['dist_sqr'][n]
            proxy_mean = proxy_mean[np.where(proxy_mean != 0)[0]]
            pcl_2[i]['mean_dist_sqr'][n] = np.average(proxy_mean)

    x = range(1,lag_range[1])
    count = np.zeros((lag_range[1]-1,))
    mean_msd = np.zeros((lag_range[1]-1,))

    for i in range(len(pcl_2)):
        pointer = pcl_2[i]['max_lag_num']
        if lag_range[0] <= pointer <= lag_range[1]:
            for j in range(pointer-1):
                count[j] += 1
                mean_msd[j] = mean_msd[j] + pcl[i].mean_dist_sqr[j]
    mean_msd /= count
    #mean_msd *= .166 * .166
    mean_msd[np.isnan(mean_msd)] = 0
    er = mean_msd / np.sqrt(count)

    x = np.array(x)
    y = np.array(mean_msd)
    er = np.array(er)

    return x, y, er

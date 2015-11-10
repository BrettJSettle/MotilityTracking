"""
@author: Brett Settle
@Department: UCI Neurobiology and Behavioral Science
@Lab: Parker Lab
@Date: August 6, 2015
"""
import numpy as np
from lmfit import minimize, Parameters, Parameter
from scipy.optimize import minimize as scm
import pyqtgraph as pg
from pyqtgraph.Qt import QtGui

def calculate_cdfs(par_det):
    #diffusion_ensemble,weight_slow,weight_fast
    # July 21 2014 // DS
    # take in the displacement squares & lags calculated per
    # track & return the following
    # cdfs for each lag
    # weights for the two componet and diffusion coefficents.
    # NOTE: cdfs fiels rs/rf are in pixels
    # While calculating resultant diffusion coefficents they were converted to
    # micro meter squared.

    dfg=[a['fr_length'] for a in par_det]
    max_lag=max(dfg)-1
    #
    ii=len(par_det)

    cdfs = [CDF() for i in range(max_lag)] # build a cdf for each lag num
    # cdfs is a structure that had all the displacement square reading for each
    # lag. max_lag determined by parameter utl in the main code.
    #
    for jk in range(ii):
        kk=par_det[jk]['fr_length']-1 # maximum lag in track jk
        for kk1 in range(kk): # for every lag, compile the squared distances that are greater than 0
            proxy_array=par_det[jk]['dist_sqr'][kk1]
            proxy_array=proxy_array[proxy_array>0]
            cdfs[kk1].rsqr = np.concatenate((cdfs[kk1].rsqr, proxy_array))
    #
    # calculate cdf
    for jk in range(max_lag):
        x=np.copy(cdfs[jk].rsqr)
        [xcdf,ycdf]=cal_cdf_lag(x) #Cumulative Distribution Function for each lag
        cdfs[jk].xcdf=xcdf
        cdfs[jk].ycdf=ycdf
    # Fit the cdfs and record the value of the two fractions.

    for jk in range(max_lag): # for every lag, use the cdf data in nonlinear least squares regression polynomial fit
        print("Fitting Lag %s of %s" % (jk + 1, max_lag))
        x=cdfs[jk].xcdf
        y=cdfs[jk].ycdf
        for i, vals in enumerate(fit_cdf(x,y)): # pass in x values, percent
            cdfs[jk].set_exponent_fit(i+1, *vals)

    return cdfs

    ###################################
    # Function to calculate the cdfs per lag
def cal_cdf_lag(x):
    n=len(x)
    y=np.array(range(1,n+1))/(n * 1.)
    return sorted(x), y

def fun(args, x):
    der = args['der'].value
    if der > 1:
        ws = [args['w%i' % i].value for i in range(1, der+1)]
    else:
        ws = [1]
    rs = [args['r%s' % i].value for i in range(1, der+1)]
    return 1 - sum([ws[i]*np.exp(-x/rs[i]) for i in range(der)])

def resid(par, y=None, x=None):
    error = fun(par, x)-y
    return error

    ###################################
    # Function to fit the cdfs per lag
def fit_cdf(x,y):
    # x here stands for displacement square measures.
    x=np.double(x) # to avoid warnings while running.
    for i in range(1, 4): # fit to 1/2/3 component
        cdf = Parameters()
        cdf['der'] = Parameter(value=i, vary=False)
        ws = ['w%i' % j for j in range(1, i+1)]
        rs = ['r%i' % j for j in range(1, i+1)]
        for j in range(i):
            if i > 1:
                cdf[ws[j]] = Parameter(value=1./i, min=0, max=1)
            else:
                cdf['w1'] = Parameter(value=1, vary=False)
            cdf[rs[j]] = Parameter(value=.5,  min = 0)

        try:
            ans = minimize(resid, cdf, args=(y, x))
        except:
            pass
        print(cdf)
        yield cdf, ans, [i + y for y in fun(cdf, x)]

class CDF():
    def __init__(self):
        self.rsqr = []
        self._fits = {}

    def set_exponent_fit(self, exp, cdf, fit_res, yfit):
        self._fits[exp] = {'yfit': yfit, 'gof':fit_res.__dict__['chisqr']}
        for k in cdf.keys():
            if k.startswith('w'):
                self._fits[exp]["Weight %s" % k[1:]] = cdf[k].value
            if k.startswith('r'):
                self._fits[exp]["Diff Coeff %s" % k[1:]] = cdf[k].value / (4 * exp)

    def __getitem__(self, i):
        if type(i) == tuple:
            return self._fits[i[0]][i[1]] if i[1] in self._fits[i[0]] else -1
        elif type(i) == int:
            return self._fits[i]

class CDFWidget(QtGui.QWidget):
    def __init__(self):
        super(CDFWidget, self).__init__()
        self.tracks = []
        self.cur_lag = 1
        self.plt = pg.PlotWidget()
        self.plt.setWindowTitle("CDF Graph for Lag #1")
        it = self.plt.getPlotItem()
        it.setLabel('left', text='Cumulative Distribution Function')
        it.setLabel('bottom', text='(SLD)^2 (Pixels^2)')
        self.tab = pg.TableWidget()
        self.lag_spin = pg.SpinBox(value=1, int=True, minStep=1, step=1, bounds=[1, 2])
        self.lag_spin.sigValueChanged.connect(lambda f : self.set_lag(f.value()))
        loadButton = QtGui.QPushButton('Load CDF Data')
        loadButton.clicked.connect(self.update)
        grid = QtGui.QGridLayout()
        self.setLayout(grid)
        grid.addWidget(self.plt, 0, 0, 3, 3)
        grid.addWidget(self.tab, 3, 0, 5, 3)
        grid.addWidget(loadButton, 8, 0)
        grid.addWidget(QtGui.QLabel(text="Lag Number: "), 8, 1)
        grid.addWidget(self.lag_spin, 8, 2)
        self.lg = self.plt.addLegend(offset=(100, 100))

    def setTracks(self, tracks):
        self.tracks = tracks
        self.new_tracks = True

    def set_lag(self, new):
        if new > len(self.cdfs):
            return
        self.cur_lag = new
        self.plt.setWindowTitle('CDF Graph for Lag #%s' % new)
        self.update()

    def update(self):
        if len(self.tracks) == 0:
            print("Tracks not loaded to Cumulative Distribution Widget")
            return
        if self.new_tracks:
            self.cdfs = calculate_cdfs(self.tracks)
            self.new_tracks = False
            self.lag_spin.setMaximum(len(self.cdfs) - 1)
            
        self.plt.getPlotItem().clear()
        for a in ('Data', 'Exp 1', 'Exp 2', 'Exp 3'):
            self.lg.removeItem(a)
        cdf = self.cdfs[self.cur_lag]

        xs = cdf.xcdf
        data = []
        columns = ('Diff Coeff 1', 'Diff Coeff 2', 'Diff Coeff 3', 'Weight 1', 'Weight 2', 'Weight 3')
        for i in range(1, 4):
            self.plt.addItem(pg.PlotDataItem(x=xs, y=cdf[i, 'yfit'], pen=(255 if i == 3 else 0, 255 if i == 2 else 0, 255 if i == 1 else 0), name = "Exp %s" % i))
            app = [cdf[i, a] for a in columns]
            data.append(tuple(app))
        #self.plt.plot(x = xs, y=cdf.ycdf, pen=None, symbol='t', symbolPen=None, symbolSize=1, symbolBrush=(255, 255, 255), name="Data")
        self.plt.plot(x = xs, y=cdf.ycdf, pen=(255, 255, 255), name="Data")

        self.plt.setYRange(0, 1)
        self.plt.setXRange(0, max(xs))

        data = np.array(data, dtype=[(a, float) for a in columns])
        self.tab.setData(data)

if __name__ == "__main__":
    
    ys = np.random.random(1000)
    xs = range(len(ys))
    x = np.array(xs)
    y = np.array(ys)
    from PyQt4 import QtGui
    app = QtGui.QApplication([])
    pw = pg.PlotWidget()
    pw.show()
    pw.getViewBox().setAspectLocked(True)
    for i in fit_cdf(x, y):
        pw.addItem(pg.PlotDataItem(i[2]))
    app.exec_()
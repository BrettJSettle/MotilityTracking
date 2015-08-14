#######INSTALLATION MANUAL FOR CALCIUM RELEASE TRACKING PROGRAM##########
#									#
#	AUTHOR: 	Brett Settle					#
#	DATE:		March 2, 2015					#
#	Lab:		UC Irvine Department of Neurobiology		#
#				and Behavioral Sciences			#
#	PURPOSE:	Tracking motility of calcium releases in 	#
#			cell videos (ie tif's, stk's) that exported	#
#			BIN files of XY track locatons, generating	#
#			analysis/comparing tracks to simulated data.	#
#									#
#########################################################################

Requires:
	Python 		v2.7
	numpy 		v1.9
	scipy		v0.14
	opencv-python 	v2.4
	PyQt4		(and all dependencies)
	pyqtrgaph 	v0.9
	xlrd 		v0.9
	xlwt 		v0.7

If python is not installed correctly on the computer, the automatic
install will not work. Ensure that Python 2.7 is installed and the
system environment PATH variable has the Python27 folder in it.

To install: double click the RUN.bat file located in this folder
It will automatically install the required plugins and walk through
any other necessary installations for the program to work.

Once plugins are successfully installed, the Tracking window will open.

IMPORTANT: BIN files must be generated prior to using this program, and
encrypted according to FIJI or Origin 9, to allow the Tracking program
to properly read input data.

The Menu at the top allows the used to open one or many BIN files,
add a BIN file to the analysis, import a background image/video, import
pyFLIKA generated Puff locations (average and individual), generate
simulated data in a new dock for comparison, and to export data from
any graph or dock to an excel file.

The window comprises of 2 Docks.

Dock 1 is the plot of all the tracks loaded by the user, as well as a
background image and/or any other FLIKA points imported. Options below
allow the user to show/hide the Track lines, points, and mean XY positions.
There are also options to toggle the background image, and to map the
distances from mean track locations to the closest mean FLIKA points,
or to remove respective FLIKA points from the plot.
	Right Click and drag to create ROIs, which can be used to exclude
unwanted tracks from the plot.  There is a "Show Options" checkbox which
allows for extra specializations of tracks to exclude from the analysis.


Dock 2 is the Mean Squared Distances Plot, along with a histogram of
the Mean Lag Distances. The first plot allows for specification of a
track length cutoff range, to exclude tracks that are too short or too
long (ie noise or false positives).  The bottom histogram allows the user
to change the bin count to greater analyze the histogram.
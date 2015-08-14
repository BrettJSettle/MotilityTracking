# MotilityTracking
Analyze the motility of active cell sites imported by a bin file from Origin Analysis


INTRODUCTION
------------
The MotilityTracking program displays imported coordinate paths as green lines for easy analysis.  Tracks can be excluded based on parameters like length and distance.  Statistical analysis of tracks is performed, displaying the mean squared distances of the tracks, and a histogram of mean lag distances, where each piece of a track is a 'lag'.  The lags are provided by Origin analysis and plotted for analysis using this program.


REQUIREMENTS
------------

Reliant on Python 3.4 or 2.7 (untested), preferably installed through Anaconda Scientific Library (http://continuum.io/downloads#py34) as well as several other python plugins:

Included in Anaconda:
*	PyQt 		v4	(will not install with 'pip')
*	numpy 	v1.9.2
*	scipy 	v0.16
*	scikit-learn	v0.16.1
*	xlrd		v0.9.3

Separate installs:
* lmfit     v0.8.3
* cv2
*	pyqtgraph	v0.9.10

To install plugins, open a command prompt and type 'pip install plugin-name', using the names as they appear above.

INSTALLATION
------------
To install the MotilityTracking Program, install all of the plugins listed above into your python environment, download the MotilityTracking Folder from github (https://github.com/BrettJSettle/MotilityTracking) by clicking on the 'Download Zip'
button on the right sidebar. Extract it to your computer and run by clicking the 'run.bat' file located inside the MotilityTracking Folder.


USING THE PROGRAM
-----------------
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

ABOUT
-----
*	Program: MotilityTracking
*	Author: Brett Settle
*	Date: August 13, 2016
*	Lab: UCI Parker Lab, McGaugh Hall

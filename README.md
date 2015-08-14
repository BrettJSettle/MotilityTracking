# MotilityTracking
Analyze the motility of active cell sites imported by a bin file from Origin Analysis


INTRODUCTION
------------
The MotilityTracking program displays imported coordinate paths as green lines for easy analysis.  Tracks can be excluded based on parameters like length and distance.  Statistical analysis of tracks is performed, displaying the mean squared distances of the tracks, and a histogram of mean lag distances, where each piece of a track is a 'lag'.  The lags are provided by Origin analysis and plotted for analysis using this program.


REQUIREMENTS
------------

Reliant on Python 3.4 or 2.7 (untested), preferably installed through
Anaconda Scientific Library (http://continuum.io/downloads#py34) as well
as several other python plugins:

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
To install the MotilityTracking Program, install all of the plugins listed above
into your python environment, download the MotilityTracking Folder from github
(https://github.com/BrettJSettle/MotilityTracking) by clicking on the 'Download Zip'
button on the right sidebar. Extract it to your computer and run by clicking the
'run.bat' file located inside the MotilityTracking Folder


USING THE PROGRAM
-----------------
IN PROGRESS

ABOUT
-----
*	Program: MotilityTracking
*	Author: Brett Settle
*	Date: August 13, 2016
*	Lab: UCI Parker Lab, McGaugh Hall

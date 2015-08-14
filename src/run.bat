echo off
IF "%1"=="-install" (
	call pip install -r list.txt > install.txt
	del install.txt
)
python TrackMain.py
del /S *.pyc
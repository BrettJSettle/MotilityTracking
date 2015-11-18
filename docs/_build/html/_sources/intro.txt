Introduction to Motility Tracking
**********************************
	This tracking program was created in the `Parker Lab <http://parkerlab.bio.uci.edu/index.htm>`_ to plot and analyze the motility of active points in cell movies.  The analysis is gathered from track lag data by plotting the Mean Squared Displacement Per Lag and a histogram of Mean Single Lag Distances.  Tracks can be filtered accordingly for analysis of immotile/extremely motile clusterings.

Getting Started
===================
Motility Tracking currently only supports .bin files exported from Origin. 

Steps
===================
Import a Tracks File
----------------
.. py:module:: file
.. autofunction:: open_file
.. autofunction:: save_file
Edit
----------------
Image
----------------
Stacks
+++++++++++++++++++
.. py:module:: stacks
.. autofunction:: deinterleave
.. autofunction:: slicekeeper
Process
----------------
Binary
+++++++++++++++++++
.. py:module:: binary
.. autofunction:: threshold
.. autofunction:: remove_small_blobs
Filters
+++++++++++++++++++
.. py:module:: filters
.. autofunction:: gaussian_blur
.. autofunction:: butterworth_filter
.. autofunction:: boxcar_differential_filter
Math
+++++++++++++++++++
.. py:module:: math_
.. autofunction:: subtract
.. autofunction:: ratio
.. autofunction:: multiply
Analyze
----------------

.. |Ca2+| replace:: Ca\ :sup:`2+`
.. |IP3| replace:: IP\ :sub:`3`



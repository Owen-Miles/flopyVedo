"""
Example: check out some smoothing options for geologic surfaces
useful in visual/conceptual modeling
"""
import os

import numpy as np
import pandas as pd

import matplotlib.pyplot as mplt
# from scipy.interpolate import griddata

from vedo import *

# a coarse surface:
denovian = pd.read_csv('./input_files/DenovianGeologicLayer.csv', sep=',')
# shift slightly for better rendering
denovian_s = delaunay2D(denovian.values * [1, 1, 10]).opacity(0.6).c('green').lc('black')
denovian_points = Points(denovian.values * [1, 1, 10], r=7).c('blue3')

# denovian_s2 = denovian_s.clone().smoothLaplacian(niter=20, relaxfact=0.1, edgeAngle=15, featureAngle=60)
# denovian_s3 = denovian_s.clone().smoothWSinc(niter=20, passBand=0.1, edgeAngle=15, featureAngle=60)
denovian_s3 = denovian_s.clone().subdivide(N=2, method=1).smoothWSinc().computeNormals()

plt = Plotter(N=2, axes=1, bg2='lb', size=(1000, 700))  # set up the plotter

plt.show(denovian_s, 'input surface', at=0,viewup="z", interactorStyle=10)
plt += denovian_points

plt.show(denovian_s3, 'input surface', at=1)
plt += denovian_points

plt.show(interactive=True, viewup="z",  interactorStyle=10)
"""
Example: use Vedo, pykrige to interpolate sample data across a grid of points using 3D kriging 
"""

from vedo import Plotter, Points, interpolateToVolume
from vedo.pyplot import cornerHistogram

import numpy as np
import pandas as pd
import random

# using Ordinary kriging as an example
from pykrige.ok3d import OrdinaryKriging3D
from pykrige.uk3d import UniversalKriging3D


# here is the input data,
x = [0, 2, 3, 7, 15, 8, 5, 20, 23, 30, 45, 38, 22,10]
y = [1, 5, 10, 2, 20, 10, 5, 1, 5, 10, 2, 15, 10, 5]
z = [10, 8, 11, 9, 15, 10, 15, 10, 8, 11, 9, 15, 10, 15]
val = [0, 0, 0, 0, 30, 0, 0, 0, 0, 0, 0, 30, 0, 0]


# and as pandas dataframe to easily plot it in vedo:
in_pts = pd.DataFrame(data={'x': x, 'y': y, 'z': z, 'val': val})
# plotting bit:
inpnts = Points(in_pts[["x", "y", "z"]].values,
              r=10).cmap("jet", in_pts[["val"]])

ok3d = OrdinaryKriging3D(
    x, y, z, val, variogram_model="linear",nlags=10)

# the output points
opntx = np.arange(float(min(x)), max(x), 1)  
opnty = np.arange(float(min(y)), max(y), 1)
opntz = np.arange(float(min(z)), max(z), 1)

# this will make the point x,y,z lists needed:
x1 = []
y1 = []
z1 = []
for x in opntx:
    for y in opnty:
        for z in opntz:
            x1.append(x)
            y1.append(y)
            z1.append(z)

k3d1, ss3d = ok3d.execute("points", x1, y1, z1)

out_pnts = pd.DataFrame(data={'x': x1, 'y': y1, 'z': z1, 'val': k3d1})

# Optional: look at a histogram of the output
# import matplotlib.pyplot as mpltlb
# mpltlb.hist(out_pnts[["val"]])
# mpltlb.show()

outpts = Points(out_pnts[["x", "y", "z"]].values,
                r=4).cmap("jet", out_pnts[["val"]])




plt = Plotter(axes=1, bg2='lb', size=(1000, 700))  # set up the plotter

plt += inpnts

plt += outpts.addScalarBar3D(sy=30, title='Concentration') #output points

plt.show(viewup="z", interactorStyle=10)




############# use a grid to interpolate over:
# # generate a grid of points, using three lists
# opntx = np.arange(0.0, 20.0, 1)  # note: must be float
# opnty = np.arange(0.0, 12.0, 1)
# opntz = np.arange(9.0, 16.0, 1)

# k3d1, ss3d = ok3d.execute("grid", opntx, opnty, opntz)

# # output is a 4D np array, need to fold it into x,y,z,val dataframe, heres the long way that works:
# x1 = []
# y1 = []
# z1 = []
# val1 = []
# for ix, x in enumerate(opntx):
#     for iy, y in enumerate(opnty):
#         for iz, z in enumerate(opntz):
#             x1.append(x)
#             y1.append(y)
#             z1.append(z)
#             val1.append(k3d1[iz,iy,ix]) # note the z => y => x because of array indexing.
# out_pnts = pd.DataFrame(data={'x': x1, 'y': y1, 'z': z1, 'val': val1})

# # and plot it:
# plt += Points(out_pnts[["x", "y", "z"]].values, r=4).cmap("jet", out_pnts[["val"]])
# plt.show(viewup="z", interactorStyle=10)
"""
Example: use Vedo, pykrige to interpolate sample data across a grid of points, 
compare with different volume interpolations in Vedo 
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
x = [0, 2, 3, 7, 15, 8, 5, 20, 23, 30, 45, 38, 22, 10, 30, 20]
y = [1, 5, 10, 2, 20, 10, 5, 1, 5, 10, 2, 15, 10, 5, 20, 20]
z = [10, 8, 11, 9, 15, 10, 15, 10, 8, 11, 9, 15, 10, 15, 7, 8]
val = [0, 0, 0, 0, 30, 0, 0, 0, 0, 10, 0, 30, 15, 0, 0, 0]


# and as pandas dataframe to easily plot it in vedo:
in_pts = pd.DataFrame(data={'x': x, 'y': y, 'z': z, 'val': val})
# plotting bit:
inpnts = Points(in_pts[["x", "y", "z"]].values,
                r=10).cmap("jet", in_pts[["val"]])

ok3d = OrdinaryKriging3D(
    x, y, z, val, variogram_model="linear", nlags=4)

# next, use points not a grid. Could help with some grid nonsense later.
opntx = np.arange(float(min(x))-5, max(x)+5, 1)  # note: must be float
opnty = np.arange(float(min(y))-5, max(y)+5, 1)
opntz = np.arange(float(min(z))-5, max(z)+5, 1)

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

outpts = Points(out_pnts[["x", "y", "z"]].values,
                r=4).cmap("jet", out_pnts[["val"]])


krigVol = interpolateToVolume(outpts.addPointArray(
    out_pnts[["val"]], name='val'), kernel='shepard', radius=1, dims=(60, 60, 20)).cmap("jet")

shepardVol = interpolateToVolume(inpnts.addPointArray(
    in_pts[["val"]], name='val'), kernel='shepard', radius=3, dims=(60, 60, 20)).cmap("jet")

linearVol = interpolateToVolume(inpnts.addPointArray(
    in_pts[["val"]], name='val'), kernel='linear', radius=3, dims=(60, 60, 20)).cmap("jet")

gaussianVol = interpolateToVolume(inpnts.addPointArray(
    in_pts[["val"]], name='val'), kernel='gaussian', radius=3, dims=(60, 60, 20)).cmap("jet")


plt = Plotter(N=6, axes=1, bg2='lb', size=(1000, 700))  # set up the plotter

plt.show(outpts, 'Inputs, and krig grid', viewup="z", at=0, interactorStyle=10)
plt += inpnts.addScalarBar3D(sy=30, title='Concentration')  # output points

plt.show(inpnts,'krig iso surface', at=1,)
plt += krigVol.isosurface(10)

plt.show(inpnts, 'shepard iso surface', at=2,)
plt += shepardVol.isosurface(10)

plt.show(inpnts,'linear iso surface', at=3,)
plt += linearVol.isosurface(10)

plt.show(inpnts,'gaussian iso surface', at=4,)
plt += gaussianVol.isosurface(10)

lego = krigVol.legosurface(vmin=10, cmap="jet")
plt.show(lego,'lego of krig isosurface', at=5,)

plt.show(interactive=True)

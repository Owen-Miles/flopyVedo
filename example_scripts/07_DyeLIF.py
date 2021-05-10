"""
Example: use Vedo, pykrige to interpolate some fake DyeLIF in 3D
This script does what I would normally do in EVS, but with python
It is based on this work: 
https://ngwa.onlinelibrary.wiley.com/doi/abs/10.1111/gwmr.12296
http://www.dakotatechnologies.com/services/dyelif
It takes a few minutes to run
"""

from vedo import Plotter, Points, interpolateToVolume, Lines, exportWindow
from vedo.pyplot import cornerHistogram

import numpy as np
import pandas as pd
import random

# using Ordinary kriging as an example
from pykrige.ok3d import OrdinaryKriging3D
from pykrige.uk3d import UniversalKriging3D

dye_lif_in = pd.read_csv('./input_files/DyeLIF.csv', sep=",")
# .iloc[::3] # downsample if it's slow for you

# split it up into components, useful for the kriging model:
x = dye_lif_in["X"].values
y = dye_lif_in["Y"].values
z = dye_lif_in["Z"].values
napl = dye_lif_in["napl"].values

# generate the output point grid, by dividing up each dimension.
opntx = np.arange(float(min(x)), max(x), 1)
opnty = np.arange(float(min(y)), max(y), 1)
opntz = np.arange(float(min(z)), max(z), .5)

# First step of the kriging model: calculate the kriging statistics:
ok3d = OrdinaryKriging3D(
    x, y, z, napl,
    # the spherical model is used commonly in these interpolations
    variogram_model="spherical",
    verbose=True,  # optional, I like to see the output
    enable_plotting=False,
    anisotropy_scaling_z=10)  # note anisotropy in the Z direction

# this will make the point x,y,z lists needed for the krigging output:
x1 = []
y1 = []
z1 = []
for x in opntx:
    for y in opnty:
        for z in opntz:
            x1.append(x)
            y1.append(y)
            z1.append(z)

# apply the kriging model over the points:
k3d1, ss3d = ok3d.execute("points", x1, y1, z1)

# apply the kriging model over the points:
out_pnts = pd.DataFrame(data={'x': x1, 'y': y1, 'z': z1, 'val': k3d1})

# process the kriging output: first make points then interpolate into a vedo grid:
outpts = Points(out_pnts[["x", "y", "z"]].values,
                r=6).cmap("jet", out_pnts[["val"]])

krigVol = interpolateToVolume(
    outpts.addPointArray(out_pnts[["val"]], name='val'),
    kernel='linear',
    dims=(len(opntx), len(opnty), len(opntz)),
    radius=1)
# note dims=() here is the using the same grid as the krig, so it looks nice. Not manditory, but pretty.

# For reference, lets show a linear interpolation:
dye_lif_in_pts = Points(
    dye_lif_in[["X", "Y", "Z"]].values).cmap("jet", dye_lif_in[["napl"]])
simpleInterpolate = interpolateToVolume(
    dye_lif_in_pts.addPointArray(dye_lif_in[["napl"]], name='val'),
    dims=(30, 30, 30),
    radius=1).cmap("jet")

# Plotting and output:
plt = Plotter(N=4, axes=1, bg2='lb', size=(1000, 800))  # set up the plotter

dye_lif_pnts_filt = dye_lif_in[dye_lif_in["napl"] > 0.3]

top_xyz = dye_lif_in.groupby(['Boring'], sort=False)["X", "Y", "Z"].max()
bottom_xyz = dye_lif_in.groupby(['Boring'], sort=False)["X", "Y", "Z"].min()

borings = Lines(top_xyz[["X", "Y", "Z"]].values,  # start points
                bottom_xyz[["X", "Y", "Z"]].values,  # end points
                c="blue", alpha=1, lw=2)
napl_detection = Points(
    dye_lif_pnts_filt[["X", "Y", "Z"]].values, r=3).c('red')
# .cmap("jet", dye_lif_in[["napl"]]) # for some data we may want a color map instead

plt.show(borings, viewup="z", at=0, interactorStyle=10,
         axes=dict(showTicks=False, xyGrid=False))
plt += napl_detection

# # the linear interpolation
plt.show(borings, at=1,)
plt += simpleInterpolate.isosurface(0.2).opacity(0.5).c("red")

# # Krig outputs, first blocky
plt.show(borings, at=2,)
plt += napl_detection
lego = krigVol.legosurface(vmin=0.15)
plt += lego.opacity(0.5).c("red")

# then smooth:
plt.show(borings, at=3,)
plt += napl_detection
plt += krigVol.isosurface(0.2).opacity(0.5).c("red")

plt.show(interactive=True)

# exportWindow('DyeLif.x3d') #Optional: export to html for embedding

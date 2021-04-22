
"""
Example: resample some borehole information onto a series of points on a grid
useful operation for modeling
"""

import numpy as np
import pandas as pd

from vedo import Plotter, delaunay2D, Grid, Points
from scipy.interpolate import griddata

# Create a plotter
plt = Plotter(axes=dict(xtitle='m', ytitle='m', ztitle='m (vertical ex)', yzGrid=False),
              bg2='lb', size=(1000, 700))  # screen size
v_exag = 10

#################
# TODO: read in these values from the .txt
xllcorner = 42991.5
yllcorner = 43524.1  # this is the bottom left corner:
cellsize = 50
total_x = 961*cellsize
total_y = 885*cellsize

denovian = pd.read_csv('./input_files/DenovianGeologicLayer.csv', sep=',')
denovian_s = delaunay2D(denovian.values).opacity(0.6)  # plot it
plt += denovian_s

# # make some points for the new grid:
gp = Grid(pos=(xllcorner+total_x/2, yllcorner+total_y/2, 500),
          sx=total_x,
          sy=total_y,
          resx=20,
          resy=20
          ).points()

# TODO: make a function? takes in x,y pairs and returns x,y,z's
# interpolate uses a mesh grid, so I need to make that first from the points:
xx, yy = np.meshgrid(np.unique(gp[:, 0]), np.unique(gp[:, 1]), sparse=True)

grid_z1 = griddata(
    denovian[["x", "y"]].values,  # the x,y pairs
    denovian["z"].values,
    (xx, yy), # This needs to be the meshgrid created above
    method='linear')

# output, convert back to Vedo-friendly:
x = []
y = []
z = []
for idx_y, row in enumerate(grid_z1):
    for idx_x, col in enumerate(row.T):
        x.append(xx[0, idx_x])
        y.append(yy[idx_y, 0])
        z.append(col)

denovian_resampled = pd.DataFrame(
    data={'x': x, 'y': y, 'z': z})  # make the x,y,z data frame

dnovian_resampled_points = Points(denovian_resampled.values, r=6).c('blue3')
plt += dnovian_resampled_points

for a in plt.actors:
    a.scale([1, 1, 1*v_exag])
plt.show(viewup="z", interactorStyle=10)  # check out interactor style options

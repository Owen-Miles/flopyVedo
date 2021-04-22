"""
Example: Make a flowpy Triangular grid and interpolate it onto another surface.
"""
import os
import flopy
from flopy.utils.triangle import Triangle as Triangle
# import numpy as np
import pandas as pd
import matplotlib.pyplot as mplt
from scipy.interpolate import griddata

from vedo import *

#################
xllcorner = 42991.5
yllcorner = 43524.1  # this is the bottom left corner:
cellsize = 50
total_x = 961*cellsize
total_y = 885*cellsize


workspace = './working/'
triExeName = './models/triangle.exe'
mf6ExeName = './models/mf6.exe'

active_domain = [(xllcorner, yllcorner),
                 (xllcorner, yllcorner+total_y),
                 (xllcorner+total_x, yllcorner+total_y),
                 (xllcorner+total_x, yllcorner)]

max_area = total_x*total_y/200  # hack for discretization to start

# Tringle mesh creation
tri = Triangle(angle=30, model_ws=workspace, exe_name=triExeName)
tri.add_polygon(active_domain)
tri.add_region((xllcorner+5, yllcorner+5), 0,
               maximum_area=max_area)
tri.build()

# # optional 2D plot of the triangle gird
# tri.plot(edgecolor='gray')
# mplt.show()

# Configuration of the triangular discretization modflow DISV package
cell2d = tri.get_cell2d()  # [index,cx,cy,nvert,v1,(v2),(v3)]
vertices = tri.get_vertices()  # verticy: [index, x, y]
ncpl = tri.ncpl  # number of cells per layer
nvert = tri.nvert  # number of vertex pairs

plt = Plotter(axes=7,bg2='lb', size=(1000, 700))  # set up the plotter

# the data to interpolate off of:
denovian = pd.read_csv('./input_files/DenovianGeologicLayer.csv', sep=',')
denovian_s = delaunay2D(denovian.values - [0,0,100]).opacity(0.6).c('green')   #shift slightly for better rendering
plt += denovian_s 

# # first interpolate the cell centres onto the surface
x = []
y = []
for f in cell2d:
    x.append(f[1])
    y.append(f[2])

z = griddata(
    denovian[["x", "y"]].values,  # the x,y pairs
    denovian["z"].values,
    (x, y), 
    method='linear')

cell_centres = pd.DataFrame(data={'x': x, 'y': y, 'z': z})

plt += Points(cell_centres.values, r=3).c('blue3')

# # and/or interpolate the cell verticies onto the surface
x = []
y = []
for f in vertices:
    x.append(f[1])
    y.append(f[2])
z = griddata(
    denovian[["x", "y"]].values, 
    denovian["z"].values,
    (x, y),
    method='linear')
vertices = pd.DataFrame(data={'x': x, 'y': y, 'z': z})

plt += delaunay2D(vertices.values).lc('b').lw(1).opacity(0.8)

v_exag = 10

for a in plt.actors:
    a.scale([1, 1, 1*v_exag])
plt.show( viewup="z", interactorStyle=10, interactive=True)


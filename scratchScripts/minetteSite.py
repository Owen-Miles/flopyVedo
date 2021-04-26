
import numpy as np
import pandas as pd

from vedo import *
from scipy.interpolate import griddata

import flopy
from flopy.utils.triangle import Triangle as Triangle

import matplotlib.pyplot as mplt

# Create a plotter 
plt = Plotter(axes=dict(xtitle='m', ytitle='m', ztitle='m (vertical ex)', yzGrid=False),
              bg2='lb', size=(1000,700)) # screen size
v_exag = 10

#################
#  Make the land surface: based on the example from A. Pollack, SCRF
print('load land surface...')
dem  = np.loadtxt("./input_files/dem50mEsriAscii.txt", skiprows=6)
# TODO: read in these values from the .txt
xllcorner = 42991.5
yllcorner = 43524.1 # this is the bottom left corner:
cellsize = 50
total_x = 961*cellsize
total_y = 885*cellsize

# instantiate coordinates
x = []
y = []
z = []
xcoord = xllcorner
ycoord = yllcorner + total_y #iterator will work through top letft to bottom right
# # make lists for the df, note list appending is faster than df appending
for row in dem:
    xcoord = xllcorner
    for col in row.T:
        x.append(xcoord)
        y.append(ycoord)
        z.append(col)
        xcoord += cellsize
    ycoord -= cellsize  
land_surface = pd.DataFrame(data={'x': x, 'y': y, 'z': z}).iloc[::5] # make the x,y,z data frame
#Note the iloc ::5 is taking every 5th row. A crude resample to lower run time
print('interpolate mesh of land surface...')

landSurface = delaunay2D(land_surface.values) # plot it 
zvals = landSurface.points()[:, 2] # get the z values to color it
landSurface.cmap("terrain", zvals) 
landSurface.name = "Land Surface" # give the object a name

# Plot it:
plt += landSurface 
plt += landSurface.isolines(5).lw(1).c('k').opacity(0.2)

#################
# #  Make the boreholes:
# print('load and plot boreholes...')
# bhs = pd.read_csv('./input_files/DenovianGeologicLayer.csv', sep=',')
# bores = Lines(bhs[["x", "y", "ztop"]].values, # start points
#               bhs[["x", "y", "zbot"]].values, # end points
#               c="black", alpha=1, lw=2)
# plt += bores

#################
#  Make the denovian layer:
print('load and plot denovian top...')
denovian = pd.read_csv('./input_files/DenovianGeologicLayer.csv', sep=',')
denovian_s = delaunay2D(denovian.values).opacity(0.6) # plot it 
plt += denovian_s



##############3#
# Make the triangles:

print('make triangles...')

workspace = './working/'
triExeName = './models/triangle.exe'
mf6ExeName = './models/mf6.exe'

active_domain = [(xllcorner, yllcorner),
                 (xllcorner, yllcorner+total_y),
                 (xllcorner+total_x, yllcorner+total_y),
                 (xllcorner+total_x, yllcorner)]

max_area = total_x*total_y/400  # hack for discretization to start

# Tringle mesh creation
tri = Triangle(angle=30, model_ws=workspace, exe_name=triExeName)
tri.add_polygon(active_domain)
tri.add_region((xllcorner+5, yllcorner+5), 0,
               maximum_area=max_area)
tri.build()


# Configuration of the triangular discretization modflow DISV package
cell2d = tri.get_cell2d()  # [index,cx,cy,nvert,v1,(v2),(v3)]
vertices = tri.get_vertices()  # verticy: [index, x, y]
ncpl = tri.ncpl  # number of cells per layer
nvert = tri.nvert  # number of vertex pairs

# # optional 2D plot of the triangle gird
# tri.plot(edgecolor='gray')
# mplt.show()

# # first interpolate the cell centres onto the surface
print('interpolate triangles onto denovian...')

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

denovian_top_cells = pd.DataFrame(data={'x': x, 'y': y, 'z': z})
plt += Points(denovian_top_cells.values, r=3).c('blue3')

print('interpolate triangles onto ground surface...')
z = griddata(
    land_surface[["x", "y"]].values,  # the x,y pairs
    land_surface["z"].values,
    (x, y), 
    method='linear')
surface_cells = pd.DataFrame(data={'x': x, 'y': y, 'z': z})

plt += Points(surface_cells.values, r=3).c('blue3')


###############################33
# set up simple model here
print('build GWF model...')


# vertical:
nlay = 1
top = 10.
botm = [0.] # for layers, this is an array (for multiple layers, bottoms are defined)

# properties
k=0.0001

# # ##################### Model part
name = 'mf'
sim = flopy.mf6.MFSimulation(sim_name=name, version='mf6',
                             exe_name=mf6ExeName,
                             sim_ws=workspace)
#start the simulation parameters, sim is used everywhere
# # Note, there is no storage package, therefore the model will be steady state

#set up the time steps (time discretization)
tdis = flopy.mf6.ModflowTdis(sim, time_units='SECONDS',
                             perioddata=[[100.0, 1, 1.]])
# length of time period, number of steps, and time step multiplier

# make the nam file:
gwf = flopy.mf6.ModflowGwf(sim, modelname=name, save_flows=True)

# Iterative Model Solution parameters, inner and outer
ims = flopy.mf6.ModflowIms(sim, print_option='SUMMARY', complexity='complex',
                           outer_dvclose=0.001, inner_dvclose=0.001)
                        #    outer_hclose=1.e-8, inner_hclose=1.e-8)

# discretization:
dis = flopy.mf6.ModflowGwfdisv(gwf, length_units='METERS',
                               nlay=nlay, ncpl=ncpl, nvert=nvert,
                               top=top, botm=botm,
                               vertices=vertices, cell2d=cell2d)

# Node property flow, requrired. Provides K, and what do to with saturation, at a minimum.
npf = flopy.mf6.ModflowGwfnpf(gwf, k=k)

# initial conditions, required. Simply the starting head for now.
ic = flopy.mf6.ModflowGwfic(gwf, strt=10.0)

chdList = []

# print(tri.get_edge_cells(1))
# print(tri.get_edge_cells(2))
# print(tri.get_edge_cells(3))
# print(tri.get_edge_cells(4))

leftcells = tri.get_edge_cells(4) # not 0 indexed
rightcells = tri.get_edge_cells(2)

for icpl in leftcells: chdList.append([(0, icpl), 30])
for icpl in rightcells: chdList.append([(0, icpl), 20])

chd = flopy.mf6.ModflowGwfchd(gwf, stress_period_data=chdList)

# # # drain nodes from the example:
# # drnCells = tri.get_edge_cells(5) + tri.get_edge_cells(7)
# # drnList = []
# # for icpl in drnCells: drnList.append([(0, icpl), 7.5, 0.10])
# # chd = flopy.mf6.ModflowGwfdrn(gwf, stress_period_data=drnList)

# oc = flopy.mf6.ModflowGwfoc(gwf,
#                             budget_filerecord='{}.cbc'.format(name),
#                             head_filerecord='{}.hds'.format(name),
#                             saverecord=[('HEAD', 'LAST'),
#                                         ('BUDGET', 'LAST')],
#                             printrecord=[('HEAD', 'LAST'),
#                                          ('BUDGET', 'LAST')])

sim.write_simulation()

success, buff = sim.run_simulation()


##############################

#################
# #### Vertical Ex and plot:
for a in plt.actors:
      a.scale([1, 1, 1*v_exag])
plt.show(viewup="z",interactorStyle=10) #check out interactor style options


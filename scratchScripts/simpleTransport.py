import numpy as np
import pandas as pd
# import vedo as vedo
import flopy
from flopy.utils.triangle import Triangle as Triangle

import matplotlib.pyplot as mplt

workspace = "./working/"
triExeName = "./models/triangle.exe"
mf6ExeName = "./models/mf6.exe"

tri = Triangle(exe_name=triExeName, model_ws=workspace)

domain = [
    (0, 0),
    (0, 100),
    (100, 100),
    (100, 0)
]

print('build triangles...')

tri.add_polygon(domain)
tri.add_region((10, 10), 0, maximum_area=20)
tri.build()

cell2d = tri.get_cell2d()  # [index,cx,cy,nvert,v1,(v2),(v3)]
vertices = tri.get_vertices()  # verticy: [index, x, y]
ncpl = tri.ncpl  # number of cells per layer
nvert = tri.nvert  # number of vertex pairs

# # optional 2D plot of the triangle gird
tri.plot(edgecolor='red')
mplt.show()

print('build GWF model...')


# vertical:
nlay = 1
top = 10.
# for layers, this is an array (for multiple layers, bottoms are defined)
botm = [0.]

# properties
k = 0.0001

name = 'mfsimple'

sim = flopy.mf6.MFSimulation(sim_name=name, version="mf6",
                             exe_name=mf6ExeName, sim_ws=workspace
                             )

# time domain
tdis = flopy.mf6.ModflowTdis(sim, time_units='SECONDS',
                             perioddata=[[100.0, 1, 1.]])

gwf = flopy.mf6.ModflowGwf(sim, modelname=name, save_flows=True)

ims = flopy.mf6.ModflowIms(sim, print_option='SUMMARY', complexity='complex',
                           outer_dvclose=0.0001, inner_dvclose=0.0001)


# discretization:
dis = flopy.mf6.ModflowGwfdisv(gwf, length_units='METERS',
                               nlay=nlay, ncpl=ncpl, nvert=nvert,
                               top=top, botm=botm,
                               vertices=vertices, cell2d=cell2d)

# Node property flow, requrired. Provides K, and what do to with saturation, at a minimum.
npf = flopy.mf6.ModflowGwfnpf(gwf, k=k)


ic = flopy.mf6.ModflowGwfic(gwf, strt=10.0)

# make boundaries
chdList = []
leftcells = tri.get_edge_cells(4) # not 0 indexed
rightcells = tri.get_edge_cells(2)

for icpl in leftcells: chdList.append([(0, icpl), 30])
for icpl in rightcells: chdList.append([(0, icpl), 20])

chd = flopy.mf6.ModflowGwfchd(gwf, stress_period_data=chdList)

sim.write_simulation()

success, buff = sim.run_simulation()
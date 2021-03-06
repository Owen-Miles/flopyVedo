'''
Example: Generate flowpy trianges, and interpolate top and bottom 
elevations from two surfaces.
Display the triangles and explode the surfaces.
'''
import numpy as np
import pandas as pd
import vedo as vd
from scipy.interpolate import griddata
import flopy
from flopy.utils.triangle import Triangle as Triangle
import matplotlib.pyplot as mplt


# Domain:
xllcorner = 42991.5
yllcorner = 43524.1
cellsize = 50
total_x = 961*cellsize
total_y = 885*cellsize

plt = vd.Plotter(axes=dict(xtitle='m', ytitle='m', ztitle='m 10:1 (V:H)', yzGrid=False),
                 bg2='lb', size=(1000, 700))  # screen size
v_exag = 10

# the sufcace to interpolate onto:
denovian = pd.read_csv('./input_files/DenovianGeologicLayer.csv', sep=',')
denovian_s = vd.delaunay2D(denovian.values  - [0,0,1800])
plt += denovian_s.c('green2')

# Ground surface: an ESRI Ascii grid. Here's how to convert it to something usable:
dem = np.loadtxt("./input_files/dem50mEsriAscii.txt", skiprows=6)
# instantiate coordinates
x = []
y = []
z = []
xcoord = xllcorner
ycoord = yllcorner + total_y  # iterator will work through top letft to bottom right
# # make lists for the df, note list appending is faster than df appending
for row in dem:
    xcoord = xllcorner
    for col in row.T:
        x.append(xcoord)
        y.append(ycoord)
        z.append(col)
        xcoord += cellsize
    ycoord -= cellsize
land_surface = pd.DataFrame(
    data={'x': x, 'y': y, 'z': z}).iloc[::20]  # note this last bit a crude resample to 1:20 points, because we really don't need huge resolution

landSurface = vd.delaunay2D(land_surface.values + [0,0,1000]) # plot it
zvals = landSurface.points()[:, 2] # get the z values to color it
landSurface.cmap("terrain", zvals)
plt += landSurface.opacity(.8)

workspace = './working/'
triExeName = './models/triangle.exe'
active_domain = [(xllcorner, yllcorner),
                 (xllcorner, yllcorner+total_y),
                 (xllcorner+total_x, yllcorner+total_y),
                 (xllcorner+total_x, yllcorner)]
max_area = total_x*total_y / 300  # Discretization: 300 triangles

# Tringle mesh creation
tri = Triangle(angle=30, model_ws=workspace, exe_name=triExeName)
tri.add_polygon(active_domain)
tri.add_region((xllcorner+5, yllcorner+5), 0,
               maximum_area=max_area)
tri.build()

cell2d = np.array(tri.get_cell2d())  # [index,cx,cy,nvert,v1,(v2),(v3)]
vertices = np.array(tri.get_vertices())  # verticy: [index, x, y]
ncpl = tri.ncpl  # number of cells per layer
nvert = tri.nvert  # number of vertex pairs
# get the coordinates of the cell centers:
x = cell2d[:, 1]
y = cell2d[:, 2]
# interpolate cell centers onto the Denovian:
z = griddata(
    denovian[["x", "y"]].values,  # the x,y pairs
    denovian["z"].values,
    (x, y),
    method='linear')
denovian_top_cells = pd.DataFrame(data={'x': x, 'y': y, 'z': z})

vertices2 = []
cellIndexs2 = []
for idx, cell in enumerate(np.hstack((cell2d, denovian_top_cells))):
    for vert in cell[4:7]:
        vertices2.append(
            [vertices[int(vert), 1],
             vertices[int(vert), 2],
             cell[9]])
    cellIndexs2.append([idx*3, idx*3+1, idx*3+2])

# interpolate points onto the land surface:
z = griddata(
    land_surface[["x", "y"]].values,  # the x,y pairs
    land_surface["z"].values,
    (x, y),
    method='linear')
land_surface_top_cells = pd.DataFrame(data={'x': x, 'y': y, 'z': z})

vertices3 = []
cellIndexs3 = []
for idx, cell in enumerate(np.hstack((cell2d, land_surface_top_cells))):
    for vert in cell[4:7]:
        vertices3.append(
            [vertices[int(vert), 1],
             vertices[int(vert), 2],
             cell[9]])
    cellIndexs3.append([idx*3, idx*3+1, idx*3+2])


layer_vert = np.vstack((vertices2, vertices3))

layer_cell = []
length = len(vertices2)

for idx, cell in enumerate(cellIndexs2):
    layer_cell.append([cell[0],
                       cellIndexs3[idx][0]+length,
                       cellIndexs3[idx][1]+length,
                       cell[1]])
    layer_cell.append([cell[2],
                       cellIndexs3[idx][2]+length,
                       cellIndexs3[idx][1]+length,
                       cell[1]])
    layer_cell.append([cell[0],
                       cellIndexs3[idx][0]+length,
                       cellIndexs3[idx][2]+length,
                       cell[2]])
    layer_cell.append([cell[0],
                       cellIndexs3[idx][0]+length,
                       cellIndexs3[idx][2]+length,
                       cell[2]])
    layer_cell.append([cell[0], cell[1], cell[2]])
    layer_cell.append([cellIndexs3[idx][0]+length,
                    cellIndexs3[idx][1]+length,
                    cellIndexs3[idx][2]+length])

layer_mesh = vd.Mesh([layer_vert, np.array(layer_cell,dtype=object)])
plt += layer_mesh.c('yellow3').opacity(0.8)
plt += layer_mesh.clone().wireframe().c('blue')

for a in plt.actors:
    a.scale([1, 1, 1*v_exag])
plt.show(viewup="z", interactorStyle=10)

# vd.exportWindow('floPyTriangles.x3d') #Optional: export to html for embedding

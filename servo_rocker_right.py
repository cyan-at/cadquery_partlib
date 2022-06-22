import numpy as np

import cadquery as cq

X = 0
Y = 1
DIA = 2
DEPTH = 3

M3 = 3
M4 = 4 - 2*0.1
M5 = 5

# The dimensions of the box. These can be modified rather than changing the
# object's code directly.
length = 116.0
height = 20.0
thickness = 10.0

# Create a box based on the dimensions above and add a 22mm center hole
result = cq.Workplane("XY").moveTo(-length / 2, -height / 2).box(85, height, thickness, centered=False)

# shave the sides
result = result.faces(">Z").workplane().moveTo(length / 2, -height / 2).rect(90.0, 20.0).cutBlind(-height)
result = result.faces(">Z").workplane().moveTo(-length / 2, -height / 2).rect(35.0, 20.0).cutBlind(-height)

result = result\
    .faces(">Z")\
    .workplane()\
    .moveTo(y=0, x=-23)\
    .slot2D(length=28, diameter=15, angle=0)\
    .cutBlind(-thickness)

# servo horn groove
# result = result.faces(">Z").workplane().moveTo(0, 0).circle(8).cutBlind(-5)

# servo horn holes
axis = [0.0]
holes = np.zeros((len(axis), 4))
holes[:, 0] = axis
holes[:, 2] = M5
for coord in holes:
    x = coord[X]
    y = coord[Y]
    if coord[DEPTH] > 0.0:
        result = result.faces(">Z").workplane()\
        .pushPoints([[x, y]])\
        .hole(coord[DIA], depth=coord[DEPTH])
    else:
        result = result.faces(">Z").workplane()\
        .pushPoints([[x, y]])\
        .hole(coord[DIA])

# plate holes
result = result.faces("<Y").workplane().moveTo(20, -5).hole(M4)
result = result.faces("<Y").workplane().moveTo(-50, -5).hole(M4)

result =  result.edges("|Z").fillet(1.0)

cq.exporters.export(result,"./%s.stl" % ("rocker_right"))
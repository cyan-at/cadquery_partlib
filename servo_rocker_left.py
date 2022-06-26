import numpy as np

import cadquery as cq

############################################

X = 0
Y = 1
DIA = 2
DEPTH = 3

M3 = 3 - 2*0.1
M4 = 4 - 2*0.1
M5 = 5 - 2*0.1

############################################

left = -25
right = 25
margin_left = 15
margin_right = 10

length = (right - left) + margin_left + margin_right
height = 20.0
thickness = 10.0

############################################

result = cq.Workplane("XY")\
    .moveTo(left - margin_left, -height / 2)\
    .box(length, height, thickness, centered=False)

############################################

# shave the sides
# non-horn side
result = result.faces(">Z").workplane()\
    .moveTo((right + margin_right), -height / 2)\
    .rect(length * 0.6, height)\
    .cutBlind(-thickness)

# horn side
result = result.faces(">Z").workplane()\
    .moveTo((left - margin_left) * 0.7, -height * 0.7)\
    .rect(left, height)\
    .cutBlind(-thickness)

############################################

# servo horn groove, it is nominally 2.5mm tall
result = result.faces(">Z").workplane().moveTo(0, 0).circle(9).cutBlind(-2.5)

# the extrude is not necessary, could collide
# result = result.faces(">Z").workplane().moveTo(0, 0).circle(4.5).extrude(-2)

############################################

# servo horn holes
axis = [0.0, -13, -35]
holes = np.zeros((len(axis), 4))
holes[:, 0] = axis
holes[:, 2] = M3
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

############################################

# plate holes
result = result.faces("<Y").workplane()\
    .moveTo(left, -thickness/2).hole(M4)

result = result.faces("<Y").workplane()\
    .moveTo(right, -thickness/2).hole(M4)

############################################

result =  result.edges("|Z").fillet(1.0)

############################################

cq.exporters.export(result,"./%s.stl" % ("rocker_left"))

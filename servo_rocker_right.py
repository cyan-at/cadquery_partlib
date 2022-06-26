import numpy as np

import cadquery as cq

from servo_rocker_left import X, Y, DIA, DEPTH
from servo_rocker_left import M3, M4, M5
from servo_rocker_left import left, right, margin_left, margin_right, length, height, thickness

############################################

result = cq.Workplane("XY")\
    .moveTo((left - margin_left), -height / 2)\
    .box(length, height, thickness, centered=False)

############################################

# shave the sides
# non-horn side
result = result.faces(">Z").workplane()\
    .moveTo((right + margin_right) * 0.9, -height * 0.4)\
    .rect(length * 0.65, height)\
    .cutBlind(-thickness)

# horn side
result = result.faces(">Z").workplane()\
    .moveTo((left - margin_left) * 0.9, -height * 0.4)\
    .rect(length * 0.75, height)\
    .cutBlind(-thickness)

############################################

'''
result = result\
    .faces(">Z")\
    .workplane()\
    .moveTo(y=0, x=-23)\
    .slot2D(length=28, diameter=15, angle=0)\
    .cutBlind(-thickness)
'''

############################################

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

############################################

# plate holes
result = result.faces("<Y").workplane()\
    .moveTo(left, -thickness/2).hole(M4)

result = result.faces("<Y").workplane()\
    .moveTo(right, -thickness/2).hole(M4)

############################################

result =  result.edges("|Z").fillet(1.0)

############################################

cq.exporters.export(result,"./%s.stl" % ("rocker_right"))

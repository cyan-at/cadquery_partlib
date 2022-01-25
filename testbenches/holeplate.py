#!/usr/bin/env python3

'''
USAGE: ./holeplate.py
    --o name_of_part
    --scale
    --holes <list of cartesian coords> (x, y, diameter, depth)
i.e.

'''

import numpy as np, math

import cadquery as cq

import sys
sys.path.insert(0,'..')
from cadquery_common import *

import argparse
parser = argparse.ArgumentParser()
parser.add_argument('--scale',
    type=float,
    default=1.0,
    required=False)
parser.add_argument('--o',
    type=str,
    default='routerplate_pilot')

####################################################################

parser.add_argument('--holes',
    type=str,
    default=" 0.0, 0.0, 3.0,-0.5;50.0,0.0,3.0,-0.5;50,70.0,3.0,-0.5;0.0,70.0,3.0,-0.5")

####################################################################

args = parser.parse_args()

#################################################################### deserialize, resolve all parameters

cartesian_data = np.array(Util.parse_float_str(args.holes.strip()))

# holes for ender
center_xy2 = [25.0, 35.0]
ender_holes = np.array([
    [center_xy2[0] - 10.0, center_xy2[1] + 10.0, 3.0, -0.5],
    [center_xy2[0] + 10.0, center_xy2[1] + 10.0, 3.0, -0.5],
    
    [center_xy2[0] - 10.0, center_xy2[1] - 10.0, 3.0, -0.5],
    [center_xy2[0] + 10.0, center_xy2[1] - 10.0, 3.0, -0.5],
])
cartesian_data = np.vstack([
    cartesian_data, 
    ender_holes
])

# drake 611 plate holes
drake_center = [25.0, -20.0]
drake_hole_spacing = 70.0 / 2
drake_holes = np.array([
    [drake_center[0] - drake_hole_spacing, drake_center[1], 4.0, -0.5],
    [drake_center[0] + drake_hole_spacing, drake_center[1], 4.0, -0.5],
    
    [drake_center[0] - drake_hole_spacing, 70.0, 4.0, -0.5],
    [drake_center[0] + drake_hole_spacing, 70.0, 4.0, -0.5],
])
cartesian_data = np.vstack([
    cartesian_data, 
    drake_holes
])

# pre-emptive hole set 1
center_xy = [25.0, 0] # can't use 15 because of singularity somewhere?
spacing_x = 25.0
spacing_y = 15.0
delta = np.array([[center_xy[0] - spacing_x, center_xy[1] - spacing_y, 3.0, -0.5],
    [center_xy[0] - spacing_x, center_xy[1] + spacing_y, 3.0, -0.5],
    [center_xy[0] + spacing_x, center_xy[1] - spacing_y, 3.0, -0.5],
    [center_xy[0] + spacing_x, center_xy[1] + spacing_y, 3.0, -0.5]])
cartesian_data = np.vstack([
    cartesian_data,
    delta
])

cartesian_coords = cartesian_data[:, :2] * args.scale

# dimensions, in mm, cadquery works in meters
dims = {
    "f" : 0.125, # fillet radius
    "t" : 1, # thickness
}
for k, v in dims.items():
    dims[k] = dims[k] * args.scale

##########################

# make hull, inflate with radius, and fillet
hull = None
try:
    hull, _, _ = GeoUtil.ch_gift_wrapping_jarvis_march(cartesian_coords)
except Exception as e:
    '''need to handle n = 1, n = 2 where no hull is possible'''
    print(e)

fs = [1.2] * len(hull)
new_hull = GeoUtil.inflate_hull_00(hull, fs)

result = cq.Workplane("front")
result = result.polyline([x[:2] for x in new_hull]).close()
result = result.extrude(1.0)

#result = cq.Workplane("XY" ).box(50, 50, dims["t"])
#result = result.edges("|Z").fillet(dims["f"])

for coord in cartesian_data:
    x = coord[0]
    y = coord[1]
    if coord[3] > 0.0:
        result = result.faces(">Z").workplane()\
        .pushPoints([[x, y]])\
        .hole(coord[2], depth=coord[3])
    else:
        result = result.faces(">Z").workplane()\
        .pushPoints([[x, y]])\
        .hole(coord[2])

slot_center_xy = center_xy2
slot_center_xy[1] += 20.0
result = result.faces(">Z").workplane()\
    .pushPoints([slot_center_xy])\
    .slot2D(30.0, 10.0, 90.0).cutBlind("last")

drake_slot_len = 70.0 - drake_holes[0][1]
result = slot_from(result, drake_holes[0][:2], drake_holes[0][:2] + [0.0, drake_slot_len], 4.0, inclusive = True)
result = slot_from(result, drake_holes[1][:2], drake_holes[1][:2] + [0.0, drake_slot_len], 4.0, inclusive = True)

#################################################################### produce

try:
    cq.cqgi.ScriptCallback.show_object(result)
except:
    pass

if len(args.o) > 0:
    cq.exporters.export(result,"./%s.stl" % (args.o))
    cq.exporters.export(result.section(),"./%s.dxf" % (args.o))
    print("saved %s" % (args.o))
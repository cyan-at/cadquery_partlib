#!/usr/bin/env python3

import numpy as np

import cadquery as cq

from cadquery_common import *

import argparse
parser = argparse.ArgumentParser()
parser.add_argument('--scale',
    type=float,
    default=1.0,
    required=False)
parser.add_argument('--o',
    type=str,
    default='')

####################################################################

parser.add_argument('--holes_l',
    type=int,
    default=2)

parser.add_argument('--holes_r',
    type=int,
    default=0)

####################################################################

args = parser.parse_args()

#################################################################### deserialize, resolve all parameters

# dimensions, in mm, cadquery works in meters
dims = {
    "w1": 30, # width
    "l" : 80, # length
    
    "w2": 5, # slot diameter
    "s1": 15, # spacing btwn holes and slot

    "d" : 5, # hole diameter

    "t" : 7, # thickness
    
    "f" : 0.0, # fillet radius
}
for k, v in dims.items():
    dims[k] = dims[k] * args.scale
    
##########################

result = cq.Workplane(cq.Plane.XY())\
    .box(length=dims["l"], width=dims["w1"], height=dims["t"], centered=False)
        
if dims["f"] > 0.0:
    result =  result.edges("|Z").fillet(dims["f"])
    
##########################
    
slot_length = dims["l"] - 2 * dims["s1"]
slot_origin = [dims["l"] / 2, dims["w1"] / 2]

if args.holes_l == 0:
    slot_origin[0] -= dims["s1"] / 2
    slot_length += dims["s1"] / 2
    
if args.holes_r == 0:
    slot_origin[0] += dims["s1"] / 2
    slot_length += dims["s1"] / 2
    
result = result\
    .faces(">Z")\
    .workplane()\
    .moveTo(y=slot_origin[1], x=slot_origin[0])\
    .slot2D(length=slot_length, diameter=dims["w2"], angle=0)\
    .cutBlind(-dims["t"])
    
##########################

center_x = dims["l"] / 2
gap_x = (dims["l"] - 2*dims["s1"]) / 2

hole_center_x_l = gap_x / 2
hole_center_y_offset = dims["w1"] / 4.0

hole_centers = []

if args.holes_l > 0:
    # number of gaps = args.holes_l + 1 (i.e. 0 = 1, 1 = 2, 2 = 3, etc.)
    hole_ys = np.linspace(0.0, dims["w1"], args.holes_l + 2) # + 2 for 0 and w1, ignore them
    for i in range(1, args.holes_l + 1):
        hole_centers.extend([
            [dims["s1"] / 2, hole_ys[i]],
        ])
        
if args.holes_r > 0:
    # number of gaps = args.holes_l + 1 (i.e. 0 = 1, 1 = 2, 2 = 3, etc.)
    hole_ys = np.linspace(0.0, dims["w1"], args.holes_r + 2) # + 2 for 0 and w1, ignore them
    for i in range(1, args.holes_r + 1):
        hole_centers.extend([
            [dims["s1"] + slot_length + dims["s1"] / 2, hole_ys[i]],
        ])

if args.holes_l > 0 or args.holes_r > 0:
    result = result\
        .faces(">Z")\
        .workplane()\
        .pushPoints(hole_centers).circle(dims["d"]).hole(dims["t"])

#################################################################### produce

try:
    cq.cqgi.ScriptCallback.show_object(result)
except:
    pass

if len(args.o) > 0:
    cq.exporters.export(result,"./%s.stl" % (args.o))
    cq.exporters.export(result.section(),"./%s.dxf" % (args.o))
    print("saved %s" % (args.o))

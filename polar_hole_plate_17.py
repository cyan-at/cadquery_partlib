#!/usr/bin/env python3

'''
USAGE: ./polar_hole_plate.py
    --o name_of_part
    --scale

    --ri <radius of hole>
    --ro <radius of shell>
    --t <thickness>
    --h1 <buffer_height>
    --aux <list of aux holes in polar coords: (r, theta, diameter, depth)
        theta = 0 being '12 o'clock'
'''

import numpy as np

import cadquery as cq

from cadquery_common import *

import argparse

####################################################################

parser = argparse.ArgumentParser()
parser.add_argument('--scale',
    type=float,
    default=1.0,
    required=False)
parser.add_argument('--o',
    type=str,
    default='')

parser.add_argument('--ri',
    type=float,
    default=3.0)
parser.add_argument('--ro',
    type=float,
    default=10.0)
parser.add_argument('--t',
    type=float,
    default=5.0)
parser.add_argument('--h1',
    type=float,
    default=5.0)

parser.add_argument('--h2',
    type=float,
    default=5.0)
parser.add_argument('--h3',
    type=float,
    default=10.0)

parser.add_argument('--s1',
    type=float,
    default=4.0)
parser.add_argument('--ns',
    type=int,
    default=3)
parser.add_argument('--s2',
    type=float,
    default=3.0)

parser.add_argument('--aux',
    type=str,
    default="6.0,0.0,3.0,-0.5;6.0,2.0944,3.0,-0.5;6.0,-2.0944,3.0,-0.5")

args = parser.parse_args()

polar_coords = parse_polarcoords(args.aux)
print(polar_coords)

#################################################################### deserialize, resolve parameters

# dimensions, in mm, cadquery works in meters
dims = {
    "ri": args.ri, # inner hole, if 0 ignore
    "ro" : args.ro, # extrusion radius
    "t": args.t, # thickness
    "h1": args.h1, # height of plate under the circular part

    # for the support plate
    "h2" : args.h2, # thickness
    "h3" : args.h3, # deepness

    # arguments for make_holes_along_axis_01
    "s1" : args.s1, # side spacing
    "ns" : args.ns, # number of holes
    "s2" : args.s2, # hole diameter
}
for k, v in dims.items():
    dims[k] = dims[k] * args.scale
    
l = dims["h1"] + dims["ro"]
w = dims["ro"] * 2

##########################

# # make rectangular plate under circle extrusion
result = cq.Workplane("front")\
    .box(length=l,
         width=w,
         height=dims["t"],
         centered=False)
# make circle extrusion
result = result.faces(">Z").workplane()\
    .moveTo(l, dims["ro"])\
    .circle(dims["ro"])\
    .extrude(-dims["t"])
# make circle hole
result = result.faces(">Z").workplane()\
    .moveTo(l, dims["ro"])\
    .hole(dims["ri"] * 2)
# make polar coord holes
for coord in polar_coords:    
    # (r, theta, diameter, depth), theta = 0 being 'right'
    x, y = polar_to_cartesian(coord[0], coord[1])
    
    x += l
    y += dims["ro"]
    
    print(x)
    print(y)
    print(coord[2])
    print(coord[3])

    if coord[3] > 0.0:
        result = result.pushPoints([[x, y]])\
        .hole(coord[2], depth=coord[3])
    else:
        result = result.pushPoints([[x, y]])\
        .hole(coord[2])

'''
# make support holes on plate
result = holes_along_axis_00(
        result.faces(">Z").workplane(),
        [dims["h1"] / d2, 0.0],
        1,
        dims["ro"] * 2,

        dims["s1"] * 2,
        int(dims["ns"]),

        dims["s2"])
'''

# make right angle support plate
result = result.faces(">Z").workplane()\
    .moveTo(0.0, 0.0)\
    .box(length=dims["h2"],
         width=dims["ro"] * 2,
         height=dims["h3"],
         centered=False)
# make support holes
result = holes_along_axis_00(
        result.faces(">X").workplane(),
        [0.0, dims["h3"] / 2],
        0,
        dims["ro"] * 2,

        dims["s1"],
        int(dims["ns"]),

        dims["s2"])

#################################################################### produce

# try:
#     cq.cqgi.ScriptCallback.show_object(result)
# except:
#     pass

# if len(args.o) > 0:
#     cq.exporters.export(result,"./%s.stl" % (args.o))
#     cq.exporters.export(result.section(),"./%s.dxf" % (args.o))
#     print("saved %s" % (args.o))

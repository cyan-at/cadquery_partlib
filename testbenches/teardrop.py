#!/usr/bin/env python3

'''
USAGE: ./teardrop.py
    --o name_of_part
    --scale
i.e.

'''

import numpy as np, math

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

####################################################################

args = parser.parse_args()

#################################################################### deserialize, resolve all parameters

# dimensions, in mm, cadquery works in meters
dims = {
    "w1": 30, # width
    "l" : 80, # length
    
    "w2": 5, # slot diameter
    "s1": 15, # spacing btwn holes and slot

    "t" : 1, # thickness
    
    "sl" : 10, # slot length
    "sa" : 120, # slot angle

    # diameter should != length
    "sd" : 3, # slot diameter
    "hd" : 5, # hole diameter

    
    "f" : 0.125, # fillet radius
}
for k, v in dims.items():
    dims[k] = dims[k] * args.scale
    
##########################

result = cq.Workplane("XY" ).box(50, 50, dims["t"])
result = result.edges("|Z").fillet(dims["f"])
result = result.faces(">Z").workplane()

result = make_teardrop(result,
    0.0,
    0.0,
    dims["sl"],
    dims["sd"],
    dims["sa"],
    dims["hd"],
    dims["t"])

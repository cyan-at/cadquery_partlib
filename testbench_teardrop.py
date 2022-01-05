#!/usr/bin/env python3

'''
USAGE: ./holes_along_axii_57.py
    --o name_of_part
    --scale

    --ri <radius of hole>
    --ro <radius of shell>
    --t <thickness>
    --h1 <buffer_height>
    --aux <list of aux holes in polar coords: (r, theta, diameter, depth)
        theta = 0 being '12 o'clock'
    --aux2 <list of cartesian coords> (x, y, diameter, depth)
i.e.

'''

import numpy as np, math

import cadquery as cq

from cadquery_common import *

class GeoUtils:
    @staticmethod
    def two_d_make_x_y_theta_hom(x, y, theta):
        hom = np.eye(3)

        theta = theta % (2 * np.pi)
        # 2019-08-02 parentheses!!!

        hom[0, 0] = math.cos(theta)
        hom[0, 1] = -math.sin(theta)
        hom[1, 0] = math.sin(theta)
        hom[1, 1] = math.cos(theta)

        hom[0, 2] = x
        hom[1, 2] = y
        return hom

def make_teardrop(workplane, x, y, sl, sd, sa, hd, depth):
    result = workplane.moveTo(x=x, y=y)
    result = result.slot2D(length = sl, diameter = sd, angle=sa) # diameter should != length
    result = result.cutBlind(-depth)
    
    hom1 = GeoUtils.two_d_make_x_y_theta_hom(x, y, sa * np.pi / 180.0)
    x = np.dot(hom1, np.array([sl / 2 - hd / 2, 0.0, 1.0]))
    
    result = result.moveTo(x=x[0], y=x[1])
    result = result.circle(hd / 2).cutBlind(-depth) # extrude(dims["t"])
    
    return result

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

import cadquery as cq
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

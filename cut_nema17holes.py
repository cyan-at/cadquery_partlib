#!/usr/bin/env python3


import cadquery as cq

import numpy as np, math, argparse

import sys
sys.path.insert(0,'/home/cyan3/Dev/jim/drake/software/cqpl')
from cadquery_common import *

####################################################################

def cut_nema17holes(work, center_hom2d, args, dims):
    '''
        work: <solid>.faces(">Z").workplane().workplane().moveTo(x=0, y=0)
        center_hom2d: 3x3 2d hom transform in origin frame
        args: user args including scale
        dims: dimensions

        returns: solid with cuts
    '''
    s = 31.0 * args.scale
    center_d = 22.0 * args.scale
    mount_d = 3.0 * args.scale
    for h_delta in [-s/2, s/2]:
        for v_delta in [-s/2, s/2]:
            vec = np.array([h_delta, v_delta, 1.0])
            transformed = np.dot(center_hom2d, vec)
            
            work = work.moveTo(x=transformed[0], y=transformed[1])
            work = work.circle(mount_d / 2).cutBlind(-10) # extrude(dims["t"])
    work = work.moveTo(x=center_hom2d[0, 2], y=center_hom2d[1, 2])
    work = work.circle(center_d / 2).cutBlind(-10)
    
    return work

####################################################################

parser = argparse.ArgumentParser()
parser.add_argument('--scale',
    type=float,
    default=1.0)
parser.add_argument('--o',
    type=str,
    default='nema17holes')

args = parser.parse_args()

####################################################################

# dimensions, in mm, cadquery works in meters
dims = {
    "w" : 50,
    "l" : 50,
    "h" : 5,
    "f" : 5,
}
for k, v in dims.items():
    dims[k] = dims[k] * args.scale

result = cq.Workplane("front")\
    .box(length=dims["w"],
         width=dims["l"],
         height=dims["h"],
         centered=False)
result = result.edges("|Z").fillet(dims["f"])
result = result.faces(">Z").workplane()
result = result.moveTo(x=0, y=0)

center_hom2d = GeoUtil.two_d_make_x_y_theta_hom(
    dims["w"] / 2,
    dims["l"] / 2,
    0 * np.pi / 180.0)

result = cut_nema17holes(result, center_hom2d, args, dims)


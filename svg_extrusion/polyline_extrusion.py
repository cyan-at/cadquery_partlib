#!/usr/bin/env python3

'''
given a 2d polyline of xys
create a set of 2d pill polygons to union

USAGE:
./polyline_extrusion.py --txt ./polyline.txt
'''

import numpy as np
import time, sys, os
import argparse

import cadquery as cq

from polyline_polygons import *

# parse command line
parser = argparse.ArgumentParser(description='''
''')

parser.add_argument('--scale',
    type=float,
    default=1.0,
    required=False)

#############################################

parser.add_argument('--txt',
    type=str,
    default="polyline.txt",
    help='every line is an xy')

#############################################

args = parser.parse_args()

#############################################

container = Container(args)

read_file_to_cbs(
    args.txt,
    [container.read_polyline_point])

#############################################

result = cq.Workplane("front")

extrude_dir = 1

i = 0
while i < len(container.xys)-1:
    if container.xys[i] is None or container.xys[i+1] is None:
        i += 1
        continue

    scaffold_homs = twoxys_to_six_scaffold_pts(
        container.xys[i][1:3], # xy
        container.xys[i+1][1:3], # xy
        container.xys[i][0]) # diameter
    s5, s1, s3, s6, s4, s2 = [list(x[:2, 2]) for x in scaffold_homs]


    # the CAD engine for cadquery cannot
    # handle a large polyline in any form
    # for some reason, so instead use their
    # native calls
    result = result.moveTo(*s2)
    result = result.threePointArc(s5, s1)
    result = result.lineTo(*s3)
    result = result.threePointArc(s6, s4)
    result = result.lineTo(*s2)
    result = result.close()
    result = result.extrude(0.1 * extrude_dir)

    # if there is a hole
    # then we need to select a face
    # to make a hole
    # but that means the next extrude must
    # be in the opposite direction #wide
    if len(container.xys[i]) == 4:
        result = result.faces(">Z").workplane()
        print("hole", container.xys[i][3])
        result = result.pushPoints(
            [container.xys[i][1:3]]
        )
        result = result.hole(container.xys[i][3])
        extrude_dir *= -1

    i += 1

name = "polyline_extrusion"
cq.exporters.export(result,"./%s.stl" % (name))
print("saved %s" % (name))


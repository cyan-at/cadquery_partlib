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

import svgpathtools
from svgpathtools import svg2paths2

from polyline_polygons import *

def xy_l2_norm(a, b):
    return np.sqrt(
        (a[0] - b[0])**2\
        +\
        (a[1] - b[1])**2)

def hash_xy(xy):
    return "%.2f_%.2f" % (xy[0], xy[1])

class SvgContainer(object):
    def __init__(self, args):
        self.args = args

        self.all_xys = []

        self.polylines = []
        paths, attributes, svg_attributes =\
            svg2paths2(args.svg)
        for path, attribute in zip(paths, attributes):
            polyline = [] # list of xys, broken by None
            i = 0
            while i < len(path):
                if type(path[i]) == svgpathtools.path.Line:
                    # xs = [path[i].start.real, path[i].end.real]
                    # ys = [-path[i].start.imag, -path[i].end.imag]
                    s_xy = [path[i].start.real, -path[i].start.imag]
                    e_xy = [path[i].end.real, -path[i].end.imag]

                    if len(polyline) == 0:
                        polyline.append(s_xy)

                        self.all_xys.append(s_xy)
                    else:
                        dist = xy_l2_norm(
                            polyline[-1],
                            s_xy)
                        if dist > 1e-1:
                            print("broken since s_xy != e_xy, %.3f" % (dist))
                            polyline.append(None)
                            polyline.append(s_xy)

                    self.all_xys.append(e_xy)

                    polyline.append(e_xy)
                i += 1
            if len(polyline) > 0:
                # only add routes, loops assumed to not be valid routes
                dist = xy_l2_norm(
                    polyline[0],
                    polyline[-1])
                if dist < 1e-1:
                    print("loop found")
                else:
                    self.polylines.append(polyline)

        # solve sometimes a path ends where another begins
        # so we connect them
        # TODO merge this logic into above iteration
        polylines_as_dict = {}
        # stick segments into one polyline, O(n)
        s_xy_map = {}
        e_xy_map = {}
        for j in range(len(self.polylines)):
            s_hash = hash_xy(self.polylines[j][0])
            if s_hash in s_xy_map:
                print("s_hash %s found already, this one has len %d" % (s_hash, len(self.polylines[j])))
            s_xy_map[s_hash] = j

            e_hash = hash_xy(self.polylines[j][-1])
            e_xy_map[e_hash] = j

            print("%d s_hash %s vs e_hash %s" % (j, s_hash, e_hash))

            polylines_as_dict[s_hash] = self.polylines[j]
        print("%d polylines" % len(self.polylines))
        for j in range(len(self.polylines)):
            print("%d in polyline %i" % (len(self.polylines[j]), j))
        for j in range(len(self.polylines)):
            s_hash = hash_xy(self.polylines[j][0])
            e_hash = hash_xy(self.polylines[j][-1])
            print("%d s_hash %s vs e_hash %s" % (j, s_hash, e_hash))

            if e_hash in s_xy_map.keys():
                print("found e_hash as someone's s")

                # so now we need to make sure
                # that the other polyline
                # has a s_hash that
                # is in e_xy_map for us
                k = s_xy_map[e_hash]
                other_s_hash = hash_xy(
                    self.polylines[k][0])
                k = e_xy_map[other_s_hash]
                if k == j:
                    print(len(polylines_as_dict[s_hash]))
                    print(len(polylines_as_dict[e_hash]))

                    # connect: move their start to our end
                    # note the 1: because the e_hash[0]
                    # == s_hash[-1]
                    polylines_as_dict[s_hash].extend(polylines_as_dict[e_hash][1:])
                    del polylines_as_dict[e_hash]
        self.polylines = [polylines_as_dict[x] for x in polylines_as_dict.keys()]

        # center all objects
        self.cx = np.mean([q[0] for q in self.all_xys])
        self.cy = np.mean([q[1] for q in self.all_xys])
        for k in range(len(self.polylines)):
            for j in range(len(self.polylines[k])):
                self.polylines[k][j][0] -= self.cx
                self.polylines[k][j][1] -= self.cy

# parse command line
parser = argparse.ArgumentParser(description='''
''')

parser.add_argument('--scale',
    type=float,
    default=1.0,
    required=False)

#############################################

parser.add_argument('--svg',
    type=str,
    default="pcb_test.svg",
    help='every line is an xy')

parser.add_argument('--extrude',
    type=float,
    default=5.0,
    help='')

parser.add_argument('--route_diameter_thickness',
    type=float,
    default=3.0,
    help='')

parser.add_argument('--hole_dia',
    type=float,
    default=2.4,
    help='')

#############################################

args = parser.parse_args()

#############################################

container = SvgContainer(args)

#############################################

result = cq.Workplane("front")

extrude_dir = 1

for j in range(len(container.polylines)):
    polyline = container.polylines[j]

    i = 0
    while i < len(polyline)-1:
        if polyline[i] is None or polyline[i+1] is None:
            print("none found")
            i += 1
            continue

        scaffold_homs = twoxys_to_six_scaffold_pts(
            polyline[i], # xy
            polyline[i+1], # xy
            args.route_diameter_thickness) # diameter
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
        result = result.extrude(args.extrude * extrude_dir)

        i += 1

result = result.faces(">Z").workplane()
hole_pts = [polyline[0] for polyline in container.polylines]
hole_pts.extend(
    [polyline[-1] for polyline in container.polylines]
)
result = result.pushPoints(
    hole_pts
)
result = result.hole(args.hole_dia)
extrude_dir *= -1

#############################################

name = "polyline_extrusion"
cq.exporters.export(result,"./%s.stl" % (name))
print("saved %s" % (name))
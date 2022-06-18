#!/usr/bin/env python3

'''
USAGE: ./holeplate.py
    --o name_of_part
    --scale

    --radius
    --thickness
    --hull

    --holes <list of cartesian coords> (x, y, diameter, depth)
i.e.

'''

import numpy as np, math
import sys, os, time
import select
import argparse

import cadquery as cq

sys.path.insert(0,'..')
from cadquery_common import *
import polyskel

X = 0
Y = 1
DIA = 2
DEPTH = 3

# from Util
def read_file_to_cbs(file_path, cbs):
    with open(file_path, 'r') as f:
        while True:
            line = f.readline()
            if not line:
                break
            for cb in cbs:
                cb(line)

def hole_handler(line, target_container):
    target_container.append(
        [float(x) for x in line.strip().split(",")])

#################################################################### deserialize, resolve all parameters

parser = argparse.ArgumentParser()

parser.add_argument('--scale',
    type=float,
    default=1.0,
    required=False)
parser.add_argument('--o',
    type=str,
    default="holeplate")

#############################################

parser.add_argument('--radius',
    type=float,
    default=0.5)

parser.add_argument('--thickness',
    type=float,
    default=6.0)

parser.add_argument('--hull',
    type=float,
    default=-.4)

#############################################

parser.add_argument('--holes',
    type=str,
    default="example_00.txt")

#############################################

args = parser.parse_args()

#############################################

holes = []
read_file_to_cbs(args.holes,
    [
        lambda x, holes=holes: hole_handler(x, holes)
    ])
# print(holes)

# if not select.select([sys.stdin,],[],[],0.0)[0]:
#     print("nothing pipe'd, noop")
#     sys.exit(0)
# else:
#     for line in sys.stdin:
#         tokens = line.strip().split(",")
#         holes.append([float(x) for x in tokens])

############################################# 

cartesian_data = np.array(holes)

cartesian_coords = cartesian_data[:, :2] * args.scale

# dimensions, in mm, cadquery works in meters
dims = {
    "f" : args.radius, # fillet radius
    "t" : args.thickness, # thickness
}
for k, v in dims.items():
    dims[k] = dims[k] * args.scale

####################################################################

# make hull, inflate with radius, and fillet
cw_hull_pts = None
try:
    cw_hull_pts, _, _ = GeoUtil.ch_gift_wrapping_jarvis_march(cartesian_coords)
except Exception as e:
    '''need to handle n = 1, n = 2 where no hull is possible'''
    print(e)
    sys.exit(1)

new_hull = polyskel.polygon_offset(cw_hull_pts, args.hull)
assert(len(new_hull) > 0)

#################################################################### produce

result = cq.Workplane("front")
result = result.polyline([x[:2] for x in new_hull]).close()
result = result.extrude(dims["t"])
result = result.edges("|Z").fillet(5.0)

for coord in cartesian_data:
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

# try:
#     cq.cqgi.ScriptCallback.show_object(result)
# except Exception as e:
#     print("failed to render", str(e))

if len(args.o) > 0:
    cq.exporters.export(result,"./%s.stl" % (args.o))
    cq.exporters.export(result.section(),"./%s.dxf" % (args.o))
    print("saved %s" % (args.o))

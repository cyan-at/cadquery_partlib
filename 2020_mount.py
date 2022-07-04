#!/usr/bin/env python3

'''
USAGE: ./2020_mount.py
    --scale
    --backstop
    --bottom_shave (if equal to dz, it will add a bottom ledge)
    --length
    
what i've made for laser
    ./2020_mount.py --backstop 0 --length 30 --bottom_shave 4.0
    ./2020_mount.py --backstop 1 --length 40 --bottom_shave 4.0
'''

import numpy as np, math
import sys, os, time
import select
import argparse

import cadquery as cq

X = 0
Y = 1
DIA = 2
DEPTH = 3

############################################# deserialize, resolve all parameters

# The dimensions of the box. These can be modified rather than changing the
# object's code directly.
marginx = 5.0
dy = 20.0
dz = 2.0
ledge_thickness = dz

marginx_endstop = 5
marginy_endstop_0 = 0
marginy_endstop_1 = 2
dia_endstop = 2
spacing_endstop = 14

#############################################

parser = argparse.ArgumentParser()

parser.add_argument('--scale',
    type=float,
    default=1.0,
    required=False)

parser.add_argument('--backstop',
     type=int,
     default=0)

# make this equal to dz to have the bottom ledge
parser.add_argument('--bottom_shave',
     type=float,
     default=4.0)

parser.add_argument('--length',
     type=float,
     default=30.0)

args = parser.parse_args()

#############################################

dx = args.length
bottom_shave = args.bottom_shave

#############################################

# main body
body_dx = dx
if args.backstop:
    body_dx += ledge_thickness

result = cq.Workplane("XY")\
    .moveTo(x=0, y=ledge_thickness+bottom_shave)\
    .rect(body_dx, dy + ledge_thickness-bottom_shave, centered=False)\
    .extrude(dz)

# endstop body
result = result\
    .faces(">Z")\
    .workplane()\
    .moveTo(x=0, y=dy + 2*ledge_thickness)\
    .rect(2*marginx_endstop+dia_endstop, marginy_endstop_0+marginy_endstop_1+spacing_endstop, centered=False)\
    .extrude(-ledge_thickness)
    
# endstop slot
result = result\
    .faces(">Z")\
    .workplane()\
    .moveTo(
        x=marginx_endstop+dia_endstop/2,
        y=dy+2*ledge_thickness+marginy_endstop_0+spacing_endstop/2)\
    .slot2D(length=spacing_endstop, diameter=dia_endstop, angle=90)\
    .cutBlind(-2*dz)

# nut slot
result = result\
    .faces(">Z")\
    .workplane()\
    .moveTo(y=(dy + 2*ledge_thickness)/2, x=dx/2)\
    .slot2D(length=dx-2*marginx, diameter=5.5, angle=0)\
    .cutBlind(-dz)

# bottom / top ledges
if bottom_shave == -ledge_thickness:
    result = result\
        .faces(">Z")\
        .workplane()\
        .moveTo(x=0, y=0)\
        .rect(body_dx, ledge_thickness, centered=False)\
        .extrude(ledge_thickness)

top_extrude = -ledge_thickness if (bottom_shave == -ledge_thickness) else ledge_thickness

result = result\
    .faces(">Z")\
    .workplane()\
    .moveTo(x=0, y=dy+ledge_thickness)\
    .rect(body_dx, ledge_thickness, centered=False)\
    .extrude(top_extrude)

# backstop
if args.backstop:
    result = result\
        .faces(">Z")\
        .workplane()\
        .moveTo(x=dx, y=bottom_shave+ledge_thickness)\
        .rect(ledge_thickness, dy - bottom_shave, centered=False)\
        .extrude(-ledge_thickness)
    
result = result.edges("|Z").fillet(0.5)

name = "2020_endstop_mount_%dmm_%d_%d" % (int(args.length), args.backstop, int(args.bottom_shave))
cq.exporters.export(result,"./%s.stl" % (name))
print("saved %s" % (name))

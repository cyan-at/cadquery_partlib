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

import numpy as np

import cadquery as cq

from cadquery_common import *

import argparse

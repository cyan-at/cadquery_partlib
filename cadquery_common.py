#!/usr/bin/env python3

import numpy as np

# geometry funcs

def make_a_f(xy_l, xy_r, r):
    '''
         c        d
    b   xy_l    xy_r    e
         a        f
    '''
    a = [xy_l[0], xy_l[1] - r]
    b = [xy_l[0] - r, xy_l[1]]
    c = [xy_l[0], xy_l[1] + r]
    d = [xy_r[0], xy_r[1] + r]
    e = [xy_r[0] + r, xy_r[1]]
    f = [xy_r[0], xy_r[1] - r]
    return a, b, c, d, e, f

# unit conversions to normalize before uniform scaling
mm_to_m = 1 / 1000.0
cm_to_m = 1 / 100.0
in_to_mm = 25.4
mm_to_in = 0.0393701

def parse_polarcoords(coord_str):
    '''
        all valid or nothing for now
    '''
    try:
        tokens = list(filter(lambda x: len(x) > 0, coord_str.split(";")))
        return [[float(x) for x in t.split(",")] for t in tokens]
    except Exception as e:
        print(str(e))
        return []

def parse_cartesian(coord_str):
    '''
        all valid or nothing for now
    '''
    try:
        tokens = list(filter(lambda x: len(x) > 0, coord_str.split(";")))
        return [[float(x) for x in t.split(",")] for t in tokens]
    except Exception as e:
        print(str(e))
        return []

def polar_to_cartesian(x, y, r, theta_rad):
    return x + r * np.cos(theta_rad), y + r * np.sin(theta_rad)

# generator funcs

def holes_along_axis_00(
        workplane,
        axis_proxy,
        axis_dim,
        axis_width,

        side_spacing,
        num_holes,
        
        d):
    # this function see internal semantics as such:
    # num_holes = 1 means one hole on flank0, 2 means holes @ flank0,1
    # > 2 means holes linspaced in the middle

    hole_variants = np.linspace(
        side_spacing,
        axis_width - side_spacing,
        num_holes)# should have at least 2 for the sides
    
    # spread hole variants along axis_dim, every other value is
    # left axis_proxy
    holes =\
        np.ones((num_holes, len(axis_proxy))) * axis_proxy
    holes[:, axis_dim] = -1.0 * hole_variants
    
    return workplane.moveTo(0.0, 0.0)\
    .pushPoints(holes.tolist())\
    .hole(d)
    # .circle(d / 2).extrude(1.0)

def make_teardrop(
    workplane):
    pass
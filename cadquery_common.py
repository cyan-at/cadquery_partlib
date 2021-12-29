#!/usr/bin/env python3

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
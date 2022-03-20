#!/usr/bin/env python3

import numpy as np
import math

class Util:
    @staticmethod
    def parse_float_str(s, row_delim=";", col_delim=","):
        # return [
        #     [float(y) for y in x.strip().split(col_delim)]\
        #     for x in s.strip().split(row_delim)]
        try:
            return [
                [float(y) for y in x.strip().split(col_delim)]\
                for x in s.strip().split(row_delim)]
        except Exception as e:
            print(str(e))
            return []

class GeoUtil:
    @staticmethod
    def fit_line_to_two_xy(two_xy):
        assert(len(two_xy) == 2)
        f_xy = two_xy[0]
        l_xy = two_xy[1]
        ris = l_xy[1] - f_xy[1]
        run = l_xy[0] - f_xy[0]
        if run == 0: # vertical lines
            print("vertical line")
            raise Exception("vl")
        m = ris / run
        # y = mx + b => b = y - mx
        b = f_xy[1] - m * f_xy[0]
        return [m, b]

    @staticmethod
    def xyline_midpoint(xy_line, offset = 0.0):
        # xy_line is list[2][2]
        try:
            m_and_b = GeoUtil.fit_line_to_two_xy(xy_line)
        except Exception as e:
            if (str(e)) == "vl":
                print("vl found")
                return [xy_line[0][0], (xy_line[0][1] + xy_line[1][1]) / 2.0 + offset]
        xs = list(map(lambda x: float(x[0]), xy_line)) # float is key
        avg_x = sum(xs) / len(xs)
        y = m_and_b[0]*(avg_x + offset) + m_and_b[1]
        return [(avg_x + offset), y]

    @staticmethod
    def polar_to_cartesian(x, y, r, theta_rad):
        return x + r * np.cos(theta_rad), y + r * np.sin(theta_rad)

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

    @staticmethod
    def angle_x_axis(p1, p2):
        # the set of points must be sorted in
        # increasing order of the angle they and the point P make with the x-axis.
        dy = p2[1] - p1[1]
        dx = p2[0] - p1[0]
        # if (dx == 0):
        #     return np.pi / 2
        # return math.atan(dy / dx)
        # 2018-11-15: do not use atan, atan2 more robust
        # do NOT do dx == 0 check, screws up your angle for p2 == p1
        return math.atan2(dy, dx)

        # # 2018-11-15: more explicit and reliable way about it?
        # vec_1 = GeoUtil.unit_vector_line_eq(p1, p2).tolist()
        # vec_2 = GeoUtil.unit_vector_line_eq(p1, [p1[0] + 1.0, p1[1]]).tolist()
        # theta = GeoUtil.angle_between_two_list_vecs(vec_1, vec_2)
        return theta

    @staticmethod
    def ccw(p1, p2, p3):
        # supports graham scan
        # counter-clock-wise if return > 0, clockwise if < 0, collinear if ccw = 0
        # twice the signed area of triangle formed by p1, p2, p3
        return (p2[0] - p1[0])*(p3[1] - p1[1]) - (p2[1] - p1[1])*(p3[0] - p1[0])

    @staticmethod
    def vector_line_eq(p1, p2):
        diff = np.array(p2) - np.array(p1)
        norm = np.linalg.norm(diff)
        if norm < 1e-8:
            return np.array([0.0, 0.0])

        return diff

    @staticmethod
    def ch_graham_scan(ps):
        '''
            ps : list[list[2] of [x, y]]
        '''
        # convex hull on 2d points with Graham scan
        n = len(ps)

        sorted_ps_by_y = sorted(ps, key=lambda x: x[1])
        lowest_y = sorted_ps_by_y[0] # guaranteed on hull
        # print("lowest_y", lowest_y)

        # IMPORTANT: sorted by polar angle to initial point
        by_angle = sorted(sorted_ps_by_y,
            key = lambda x: GeoUtil.angle_x_axis(lowest_y, x))
        # print("by_angle", by_angle)
        stack = []

        stack.append(by_angle[0])
        stack.append(by_angle[1])
        stack.append(by_angle[2])

        next_to_top_idx = 1
        top_idx = 2

        for i in range(3, n):
            while next_to_top_idx >= 0 and GeoUtil.ccw(
                stack[next_to_top_idx],
                stack[top_idx],
                by_angle[i]) <= 0:
                stack.pop()
                next_to_top_idx -= 1
                top_idx -= 1
            stack.append(by_angle[i])
            next_to_top_idx += 1
            top_idx += 1

        return stack, stack[0]

    @staticmethod
    def two_d_eq(p1, p2):
        if p1 is None:
            return False
        if p2 is None:
            return False
        return (p1[0] == p2[0]) and (p1[1] == p2[1])

    @staticmethod
    def find_next_gift_wrapping_point(hull_pts, not_hull_pts):
        # returns the index within not_hull_pts
        res = 0
        for i in range(1, len(not_hull_pts)):
            # if GeoUtil.two_d_left_of_line(
            #     not_hull_pts[i],
            #     hull_pts[-1], not_hull_pts[res]):
            # ccw seems to work correctly instead of 'left'
            if (GeoUtil.ccw(
                hull_pts[-1],
                not_hull_pts[res],
                not_hull_pts[i]) > 0):
                res = i
        return res

    @staticmethod
    def ch_gift_wrapping_jarvis_march(ps):
        # ps is a list of len(2) lists, 2d xys
        not_hull_pts = sorted(ps, key=lambda x: x[0], reverse = True)
        not_hull_indices = sorted(list(range(len(ps))),
            key=lambda x: ps[x][0], reverse = True)
        left_most_point = not_hull_pts[-1]
        next_pt = None
        hull_pts = []
        hull_pt_indices = []
        hull_pts.append(left_most_point)
        hull_pt_indices.append(not_hull_indices[-1])
        while not GeoUtil.two_d_eq(next_pt, left_most_point):
            q_idx = GeoUtil.find_next_gift_wrapping_point(
                hull_pts,
                not_hull_pts)
            q = not_hull_pts.pop(q_idx) # removes it as well
            hull_pts.append(q)
            hull_pt_indices.append(not_hull_indices.pop(q_idx))
            next_pt = q # eventually next_pt -> left_most_point
        return hull_pts, left_most_point, hull_pt_indices

    # https://www.seas.upenn.edu/~sys502/extra_materials/Polygon%20Area%20and%20Centroid.pdf
    @staticmethod
    def xy_closed_polygon_area(border_xys):
        # border_xys is list[n] each list[2] xy
        # and lines[0] == lines[-1] to be closed
        # print("border_xys", border_xys)
        a = 0.0000
        for i, border_xy in enumerate(border_xys[:-1]):
            # print("border_xy", border_xy)
            a += border_xy[0]*border_xys[i+1][1] - border_xys[i+1][0]*border_xy[1]
            # print("a", a)
        return a / 2.0

    # https://www.seas.upenn.edu/~sys502/extra_materials/Polygon%20Area%20and%20Centroid.pdf
    @staticmethod
    def xy_closed_polygon_centroid(border_xys):
        # border_xys is list[n] each list[2] xy
        # and lines[0] == lines[-1] to be closed
        a = GeoUtil.xy_closed_polygon_area(border_xys)
        if abs(a) < 1e-8:
            print("0 polygon area, no real centroid")
            return [0.0, 0.0], a

        cx_summation = 0.0
        cy_summation = 0.0
        for i, border_xy in enumerate(border_xys[:-1]):
            cx_summation += (border_xy[0] + border_xys[i+1][0]) * (
                border_xy[0]*border_xys[i+1][1]-border_xys[i+1][0]*border_xy[1])
            cy_summation += (border_xy[1] + border_xys[i+1][1]) * (
                border_xy[0]*border_xys[i+1][1]-border_xys[i+1][0]*border_xy[1])
        
        cx = cx_summation / (6.0*a)
        cy = cy_summation / (6.0*a)
        return [cx, cy], a

    @staticmethod
    def inflate_hull_00(hull_pts, factors, centroid = None):
        '''
        for cam like spiraling, where like so:
        # if (r_i == len(factors) - 1):
        #     break
        # fs = [factors[r_i + 1]] * len(hull_pts)
        # fs[0] = factors[r_i]
        # GeoUtil.inflate_hull_00(hull_pts, fs)
        '''
        if centroid is None:
            centroid, _ = GeoUtil.xy_closed_polygon_centroid(
                 hull_pts + [hull_pts[0]])

        new_hull = []
        for i in range(len(hull_pts)):
            vec = GeoUtil.vector_line_eq(
                centroid, hull_pts[i])

            new_hull.append(centroid + vec * factors[i])
        return new_hull

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

def make_teardrop_hole(workplane, x, y, sl, sd, sa, hd, depth):
    '''
    x y : location
    sl : slot length
    sd : slot diameter
    sa:  slot angle
    hd : hole diameter
    depth : cut depth
    '''
    result = workplane.moveTo(x=x, y=y)
    result = result.slot2D(length = sl, diameter = sd, angle=sa) # diameter should != length
    result = result.cutBlind(-depth)
    
    hom1 = GeoUtil.two_d_make_x_y_theta_hom(x, y, sa * np.pi / 180.0)
    x = np.dot(hom1, np.array([sl / 2 - hd / 2, 0.0, 1.0]))
    
    result = result.moveTo(x=x[0], y=x[1])
    result = result.circle(hd / 2).cutBlind(-depth) # extrude(dims["t"])
    
    return result

def gen_nema17holes(work, center_hom2d, args, dims):
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

def slot_from(workplane, xy_a, xy_b, diameter, inclusive = True):
    '''
        reparameterizing the cq slot function
        strategy is to get the xy midpoint of the xy_a and xy_b
        get the angle of rotation
        and feed those as the enter and angle parameters
    '''
    delta_x = xy_b[0] - xy_a[0]
    delta_y = xy_b[1] - xy_a[1]
    
    '''
    mid_xy = [
        (delta_x) / 2.0,
        (delta_y) / 2.0,
    ]
    '''    
    # offset = 0.0 if not inclusive else 0
    offset = 0.0 # irrespective of inclusive or not, just adjust length
    mid_xy = GeoUtil.xyline_midpoint([xy_a, xy_b], offset)
    norm = np.linalg.norm([delta_x, delta_y])
    length = norm if not inclusive else norm + diameter
    angle = np.arctan2(delta_y, delta_x) * 180.0 / np.pi
    print(mid_xy)
    print(length)
    print(angle)

    return workplane\
        .pushPoints([mid_xy])\
        .slot2D(
            length,
            diameter,
            angle).cutBlind("last")

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

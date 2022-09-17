#!/usr/bin/env python3

'''
given a 2d polyline of xys
create a set of 2d pill polygons to union

USAGE:
./polyline_polygons.py --txt ./polyline.txt
./polyline_polygons.py --txt ./polyline.txt --plot static
'''

import numpy as np
import time, sys, os
import argparse

import cadquery as cq

def read_file_to_cbs(file_path, cbs):
    with open(file_path, 'r') as f:
        while True:
            line = f.readline()
            if not line:
                break
            for cb in cbs:
                cb(line)

def two_d_make_x_y_theta_hom(x, y, theta):
    hom = np.eye(3)

    theta = theta % (2 * np.pi)
    # 2019-08-02 parentheses!!!

    hom[0, 0] = np.cos(theta)
    hom[0, 1] = -np.sin(theta)
    hom[1, 0] = np.sin(theta)
    hom[1, 1] = np.cos(theta)

    hom[0, 2] = x
    hom[1, 2] = y
    return hom

def smallest(th2, th1):
    # https://stackoverflow.com/questions/1878907/the-smallest-difference-between-2-angles
    a = th2 - th1
    if a > np.pi:
        a = a - 2*np.pi
    if a < -np.pi:
        a = a + 2*np.pi
    return a

def threept_arc(c_xy, s_xy, m_xy, e_xy, r, N=10):
    # compute the polar coordinate angle trajectory

    vec1 = np.array(s_xy) - np.array(c_xy)
    vec2 = np.array(m_xy) - np.array(c_xy)
    vec3 = np.array(e_xy) - np.array(c_xy)

    th1 = np.arctan2(vec1[1], vec1[0])
    th2 = np.arctan2(vec2[1], vec2[0])
    th3 = np.arctan2(vec3[1], vec3[0])

    # print("%.3f -> %.3f -> %.3f" % (th1, th2, th3))

    th2_th1 = smallest(th2, th1)
    # print("%.3f to %.3f, delta %.3f" % (th1, th2, th2_th1))

    th3_th2 = smallest(th3, th2)
    # print("%.3f to %.3f, delta %.3f" % (th2, th3, th3_th2))

    th1_th2 = np.linspace(th1, th1 + th2_th1, N)
    xys1 = np.vstack((
        c_xy[0] + r*np.cos(th1_th2),
        c_xy[1] + r*np.sin(th1_th2)
    ))
    th2_th3 = np.linspace(th2, th2 + th2_th1, N)
    xys2 = np.vstack((
        c_xy[0] + r*np.cos(th2_th3),
        c_xy[1] + r*np.sin(th2_th3)
    ))

    return np.vstack((xys1.T, xys2.T))

def twoxys_to_six_scaffold_pts(s_xy, e_xy, t):
    '''
    makes a polygon (list of xys) given a line
    and a parameter t
    '''

    # 6 scaffold points
    vec = np.array(e_xy) - np.array(s_xy)

    line_theta = np.arctan2(vec[1], vec[0])

    g_origin_sxy = two_d_make_x_y_theta_hom(s_xy[0], s_xy[1], line_theta)
    g_origin_exy = two_d_make_x_y_theta_hom(e_xy[0], e_xy[1], line_theta)

    g_sxy_s5 = two_d_make_x_y_theta_hom(-t, 0.0, 0.0)
    g_origin_s5 = np.dot(g_origin_sxy, g_sxy_s5)

    g_sxy_s1 = g_exy_s3 = two_d_make_x_y_theta_hom(0.0, t, 0.0)
    g_origin_s1 = np.dot(g_origin_sxy, g_sxy_s1)
    g_origin_s3 = np.dot(g_origin_exy, g_exy_s3)

    g_exy_s6 = two_d_make_x_y_theta_hom(t, 0.0, 0.0)
    g_origin_s6 = np.dot(g_origin_exy, g_exy_s6)

    g_sxy_s2 = g_exy_s4 = two_d_make_x_y_theta_hom(0.0, -t, 0.0)
    g_origin_s2 = np.dot(g_origin_sxy, g_sxy_s2)
    g_origin_s4 = np.dot(g_origin_exy, g_exy_s4)

    return [
        g_origin_s5,

        g_origin_s1,
        g_origin_s3,

        g_origin_s6,

        g_origin_s4,
        g_origin_s2,
    ]

def twoxys_to_pillpolygon(s_xy, e_xy, t):
    '''
    makes a polygon (list of xys) given a line
    and a parameter t
    '''

    # 6 scaffold points
    g_origin_s5,\
    g_origin_s1,\
    g_origin_s3,\
    g_origin_s6,\
    g_origin_s4,\
    g_origin_s2 = twoxys_to_six_scaffold_pts(
        s_xy, e_xy, t)

    # 6 scaffold points to polygon
    # arc between 2-5-1, 3-6-4
    # lines between 1-3 and 4-2
    s_arc_pts = threept_arc(s_xy,
        g_origin_s2[:2, 2],
        g_origin_s5[:2, 2],
        g_origin_s1[:2, 2],
        t)

    e_arc_pts = threept_arc(e_xy,
        g_origin_s3[:2, 2],
        g_origin_s6[:2, 2],
        g_origin_s4[:2, 2],
        t)

    # cw ordering
    return np.vstack((
        s_arc_pts,
        g_origin_s1[:2,2].T,
        g_origin_s3[:2,2].T,
        e_arc_pts,
        g_origin_s4[:2,2].T,
        g_origin_s2[:2,2].T
    ))

class Container(object):
    def __init__(self, args):
        self.args = args
        self.current_dia = None
        self.xys = [] # a 'ragged' 2D matrix / table

    def read_polyline_point(self, line):
        tokens = line.strip().split(",")

        if len(tokens) > 3 or len(tokens) == 0:
            print("bad line, skipping %s" % (line))
            return

        if len(tokens) == 1:
            if tokens[0] == '':
                print("disconnect found")
                self.xys.append(None)
            else:
                self.current_dia = float(tokens[0])
                print("1 token, next lines are pills of diameter %.3f" % (
                    self.current_dia))
        else:
            # must be 2 or 3
            dia_xy_andmaybeholedia = [self.current_dia]
            dia_xy_andmaybeholedia.extend([float(x) for x in tokens])
            print(dia_xy_andmaybeholedia)
            self.xys.append(dia_xy_andmaybeholedia)

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

    result = result.moveTo(*s2)
    result = result.threePointArc(s5, s1)
    result = result.lineTo(*s3)
    result = result.threePointArc(s6, s4)
    result = result.lineTo(*s2)
    result = result.close()
    result = result.extrude(0.1 * extrude_dir)

    # if there is a hole
    if len(container.xys[i]) == 4:
        result = result.faces(">Z").workplane()
        print("hole", container.xys[i][3])
        result = result.pushPoints(
            [container.xys[i][1:3]]
        )
        result = result.hole(container.xys[i][3])
        # result = result.faces("<Z").workplane()
        extrude_dir *= -1

    i += 1

name = "polyline_extrusion"
cq.exporters.export(result,"./%s.stl" % (name))
print("saved %s" % (name))


#!/usr/bin/env python3

'''
given a 2d polyline of xys
create a set of 2d pill polygons to union
'''

import numpy as np
import time, sys, os
import matplotlib.pylab as plt
import argparse

sys.path.insert(0,'/home/cyan3/Dev/jim/wall-sandbox-archive/utils_all/plotting')
import tools_2d

sys.path.insert(0,'/home/cyan3/Dev/jim/wall-sandbox-archive/utils_all/')
from utils import GeoUtil

import pyclipper, ipdb

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

flip_ccw_90 = two_d_make_x_y_theta_hom(0, 0, np.pi / 2)
flip_cw_90 = two_d_make_x_y_theta_hom(0, 0, -np.pi / 2)

def smallest(th2, th1):
    # https://stackoverflow.com/questions/1878907/the-smallest-difference-between-2-angles
    a = th2 - th1
    if a > np.pi:
        a = a - 2*np.pi
    if a < -np.pi:
        a = a + 2*np.pi
    return a

def threept_arc(c_xy, s_xy, m_xy, e_xy, r, N=100):
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

def twoxys_to_pillpolygon(s_xy, e_xy, t):
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
    # return [
    #     g_origin_s5,

    #     g_origin_s1,
    #     g_origin_s3,

    #     g_origin_s6,

    #     g_origin_s4,
    #     g_origin_s2,
    # ]

class Container(object):
    def __init__(self, args):
        self.args = args
        self.xys = []
        self.line_segs = []

    def read_polyline_point(self, line):
        tokens = line.split(",")
        if len(tokens) != 2:
            return

        e_xy = [float(x) for x in tokens]
        self.xys.append(e_xy)

if __name__ == '__main__':
    # parse command line
    parser = argparse.ArgumentParser(description='''
    ''')
    parser.add_argument('--txt',
        type=str,
        required=True,
        help='every line is an xy')
    parser.add_argument('--t',
        type=float,
        default=0.1,
        help='')

    args = parser.parse_args()

    container = Container(args)

    read_file_to_cbs(args.txt, [container.read_polyline_point])

    fig, ax = plt.subplots()
    ax.grid()
    plt.gca().set_aspect('equal',
        adjustable='box')

    sc = ax.scatter(
      [x[0] for x in container.xys],
      [x[1] for x in container.xys],
      c = [5 for x in container.xys]
    )

    ax.plot(
        [x[0] for x in container.xys],
        [x[1] for x in container.xys],
    "k")

    polygons = []
    for i in range(len(container.xys)-1):
        polygon_pts = twoxys_to_pillpolygon(
            container.xys[i],
            container.xys[i+1],
            args.t)
        polygons.append(polygon_pts)

        # ax.plot(
        #     [x[0] for x in polygon_pts],
        #     [x[1] for x in polygon_pts],
        # "k")

        fname = "polygon_%d.dat" % (i)
        np.savetxt(fname, polygon_pts,
            fmt='%1.3e',
            newline=' ')

    pc = pyclipper.Pyclipper()

    x = tuple([tuple(x) for x in polygons[0]])
    # ipdb.set_trace()

    pc.AddPath(x, pyclipper.PT_SUBJECT, True)
    # pc.AddPath(tuple([tuple(x) for x in polygons[1:]]), pyclipper.PT_SUBJECT, True)

    # clip = ((190, 210), (240, 210), (240, 130), (190, 130))
    # subj = (
    #     ((180, 200), (260, 200), (260, 150), (180, 150)),
    #     ((215, 160), (230, 190), (200, 190))
    # )

    # pc.AddPath(clip, pyclipper.PT_CLIP, True)
    # pc.AddPaths(subj, pyclipper.PT_SUBJECT, True)

    solution = pc.Execute(pyclipper.CT_UNION, pyclipper.PFT_EVENODD, pyclipper.PFT_EVENODD)

    # # import ipdb; ipdb.set_trace();

    xys = solution[0]
    # xys.append(xys[0])
    ax.plot(
        [x[0] for x in xys],
        [x[1] for x in xys],
    "k")

    plt.show()
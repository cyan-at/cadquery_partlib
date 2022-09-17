#!/usr/bin/env python3

'''
USAGE: ./svg_extrusion.py
    --scale

    --radius
    --thickness

    --svg
'''

import numpy as np, math
import sys, os, time
import select
import argparse

import cadquery as cq

sys.path.insert(0,'..')
from cadquery_common import *

import svgpathtools
from svgpathtools import svg2paths2

import matplotlib.pyplot as plt
from matplotlib.patches import Arc

class GeoUtil:
    @staticmethod
    def two_circle_intersection_points(x1, y1, r1, x2, y2, r2):
        answers = []

        # shorthand
        c1 = x1**2 - x2**2
        c2 = y1**2 - y2**2
        c3 = r1**2 - r2**2
        c4 = -2*(x1-x2)
        c5 = -2*(y1-y2)
        c6 = c1 + c2

        if c4 == 0 and c5 != 0:
            # x1 == x2, y1 != y2, still more than 1 solution maybe
            y_answer = (c3 - c6) / c5
            c8 = x1**2 + (y_answer - y1)**2 - r1**2 # c term in quadratic eq
            c9 = -2*x1 # b term in quadratic eq

            term1 = math.sqrt(c9**2 - 4*c8)
            answer_x_1 = (-c9 + term1) / 2.0
            answer_1 = [answer_x_1, y_answer]
            answers.append(answer_1)

            answer_x_2 = (-c9 - term1) / 2.0
            answer_2 = [answer_x_2, y_answer]
            answers.append(answer_2)

            return answers
        elif c4 != 0 and c5 == 0:
            # x1 != x2, y1 == y2, still more than 1 solution maybe
            x_answer = (c3 - c6) / c4
            c8 = y1**2 + (x_answer - x1)**2 - r1**2 # c term in quadratic eq
            c9 = -2*y1 # b term in quadratic eq

            term1 = math.sqrt(c9**2 - 4*c8)
            answer_y_1 = (-c9 + term1) / 2.0
            answer_1 = [x_answer, answer_y_1]
            answers.append(answer_1)

            answer_y_2 = (-c9 - term1) / 2.0
            answer_2 = [x_answer, answer_y_2]
            answers.append(answer_2)

            return answers
        elif c4 != 0 and c5 != 0:
            c9 = (c3 - c6) / c4
            c10 = -c5 / c4

            a = 1 + c10**2
            b = 2*(c9-x1)*(c10) - 2*y1
            c = (c9-x1)**2 + y1**2 - r1**2
            # print("b**2 - 4*a*c", b**2 - 4*a*c
            term0 = b**2 - 4*a*c
            if term0 < 0:
                return []
            term1 = math.sqrt(term0)

            answer_y_1 = (-b + term1) / (2.0 * a)
            answer_x_1 = c9 + c10*answer_y_1
            answer_1 = [answer_x_1, answer_y_1]
            answers.append(answer_1)

            answer_y_2 = (-b - term1) / (2.0 * a)
            answer_x_2 = c9 + c10*answer_y_2
            answer_2 = [answer_x_2, answer_y_2]
            answers.append(answer_2)

            return answers
        return []

    @staticmethod
    def find_arc_centerpoint(s_xytheta, e_xytheta, third_arc_xy, radius, threshold = 1e-3):
        # need radius to determine the problem, as well as third_arc_xy
        circle_1 = [s_xytheta[0], s_xytheta[1], radius]
        circle_2 = [e_xytheta[0], e_xytheta[1], radius]
        circles = circle_1 + circle_2
        intersections = GeoUtil.two_circle_intersection_points(*circles)
        if len(intersections) == 0:
            return []

        # once you have intersections, determine which one is within the arc
        # chord_m_and_b = GeoUtil.fit_line_to_two_xy([s_xytheta, e_xytheta])
        # midpoint_x = reduce(lambda a, b: a + b, map(
        #   lambda x: x[0], [s_xytheta, e_xytheta])) / 2.0
        # midpoint_y = chord_m_and_b[0] * midpoint_x + chord_m_and_b[1]
        # once you have the chord midpoint, you need to find point
        # on the arc that intersects the line from center of arc to midpoint
        # so now you have intersection1, chordmidpoint, arcintersection, intersection2
        # whenever intersection the chordmidpoint is in between with arcintersection
        # thats your archcenterpoint

        # alternatively, each intersection gives you a circle equation
        # and you can just check that the third_arc_xy fits on that equation

        for intersection in intersections:
            # check that (x-xc)**2 + (y-yc)**2 = r**2
            lhs = (third_arc_xy[0] - intersection[0])**2 + (third_arc_xy[1] - intersection[1])**2
            # print("lhs:", lhs)
            # print("radius**2", radius**2)
            # print("abs(lhs - radius**2)", abs(lhs - radius**2))
            if abs(lhs - radius**2) < threshold:
                # print("got it")
                return intersection

        # should not happen if arguments / problem is set up correctly
        return []

    @staticmethod
    def cartesian_to_polar(x, y):
        '''
        returns r, theta
        '''
        return np.linalg.norm([x, y]), np.arctan2(y, x)

def draw_path(fig, ax, path, attribute):
    # print(attribute)
    l = 1
    if "stroke-width" in attribute:
        l = max(l, float(attribute["stroke-width"]))
    i = 0
    last_el = None
    while i < len(path):
        if type(path[i]) == svgpathtools.path.Line:
            xs = [path[i].start.real, path[i].end.real]
            ys = [-path[i].start.imag, -path[i].end.imag]

            # then plot as 10 but should be 0.1
            # so x * 10 = 0.1
            # x = 0.1 / 10 = 0.01
            # scale by 0.01
            xs = [0.01 * j for j in xs]
            ys = [0.01 * j for j in ys]

            ax.plot(xs, ys, linewidth=l)

        elif type(path[i]) == svgpathtools.path.Arc:
            # print("Arc found")
            # import ipdb; ipdb.set_trace();

            s_xytheta = [path[i].start.real, path[i].start.imag, 0.0]
            e_xytheta = [path[i].end.real, path[i].end.imag, 0.0]
            radius = path[i].radius.real

            width = path[i].radius.real
            height = path[i].radius.imag

            if "rx" in attribute:
                print("got rx")
                ax.add_patch(
                    Arc((
                        float(attribute["cx"]) * 0.01,
                        -float(attribute["cy"]) * 0.01
                    ),
                    float(attribute["rx"]) * 0.01,
                    float(attribute["ry"]) * 0.01,
                    0,
                    theta1=0,
                    theta2=360,
                    linewidth=3.937,
                    color='red')) # draw arc
            elif "r" in attribute:
                print("got r")
                ax.add_patch(
                    Arc((
                        float(attribute["cx"]) * 0.01,
                        -float(attribute["cy"]) * 0.01
                    ),
                    float(attribute["r"]) * 0.01,
                    float(attribute["r"]) * 0.01,
                    0,
                    theta1=0,
                    theta2=360,
                    linewidth=3.937,
                    color='red')) # draw arc

            # try:
            #     center = GeoUtil.find_arc_centerpoint(s_xytheta, e_xytheta, s_xytheta, radius)

            #     dx = s_xytheta[0] - center[0]
            #     dy = s_xytheta[1] - center[1]
            #     _, theta1 = GeoUtil.cartesian_to_polar(dx, dy)

            #     dx = e_xytheta[0] - center[0]
            #     dy = e_xytheta[1] - center[1]
            #     _, theta2 = GeoUtil.cartesian_to_polar(dx, dy)

            #     theta1 = theta1 * 180 / np.pi
            #     theta2 = theta2 * 180 / np.pi

            #     # Parameters
            #     # xy(float, float)
            #     # The center of the ellipse.

            #     # widthfloat
            #     # The length of the horizontal axis.

            #     # heightfloat
            #     # The length of the vertical axis.

            #     # anglefloat
            #     # Rotation of the ellipse in degrees (counterclockwise).

            #     # theta1, theta2float, default: 0, 360
            #     width = path[i].radius.real
            #     height = path[i].radius.imag
            #     ax.add_patch(
            #         Arc((center[0], -center[1]),
            #         width,
            #         height,
            #         0,
            #         theta1=0,
            #         theta2=360,
            #         linewidth=1,
            #         color='red')) # draw arc
            # except Exception as e:
            #     print(e)

            if last_el is not None:
                if type(last_el) == svgpathtools.path.Line:
                    print("line to arc")

        last_el = path[i]
        i += 1

#################################################################### deserialize, resolve all parameters

parser = argparse.ArgumentParser()

parser.add_argument('--scale',
    type=float,
    default=1.0,
    required=False)

#############################################

parser.add_argument('--radius',
    type=float,
    default=0.5)

parser.add_argument('--thickness',
    type=float,
    default=6.0)

#############################################

parser.add_argument('--svg',
    type=str,
    default="pcb_test.svg")

#############################################

args = parser.parse_args()

#############################################

paths, attributes, svg_attributes = svg2paths2(args.svg)

# dimensions, in mm, cadquery works in meters
dims = {
    "f" : args.radius, # fillet radius
    "t" : args.thickness, # thickness
}
for k, v in dims.items():
    dims[k] = dims[k] * args.scale

####################################################################

fig, ax = plt.subplots()
ax.grid()
ax.set_aspect('equal')

for i, path in enumerate(paths):
    draw_path(fig, ax, path, attributes[i])

# import ipdb; ipdb.set_trace();

plt.show()
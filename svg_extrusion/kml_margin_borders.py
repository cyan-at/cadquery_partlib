#!/usr/local/home/cyan3/Dev/ames/viper_virtualenv/bin/python

'''
#!/usr/local/home/cyan3/Dev/ames/virtualenv3/bin/python
#!/usr/bin/python

USAGE: ./kml_margin_borders.py --kml ../../../../viper_verve_data/kml/viper-2020-01-SMG/sim-2020-02-04a.kml --dem ../../lunar_worlds/models/HermiteA_sim2.0/dem/HermiteA-sim2.0-cc_5200.00_-13195.00-dem-8192.tif

'''

import argparse
import threading
import time
import copy
import numpy as np
import sys, os

import fastkml
from fastkml import kml
from shapely.geometry import Point, LineString      
from fastkml.geometry import *
import pykml

import matplotlib
import matplotlib.pyplot as plt

from printz import *
from traverse_maker import *

def sort_and_get_indices(values_list):
    selected_indices = list(xrange(len(values_list)))
    sorted_indices = [x for _, x in sorted(
        zip(values_list, selected_indices), key=lambda pair: pair[0])]
    sorted_values = [x for x, _ in sorted(
        zip(values_list, selected_indices), key=lambda pair: pair[0])]
    return sorted_values, sorted_indices

def get_pt_param_for_line(m_and_b, pt_on_line):
    if m_and_b[0] < 1e-9:
        # horizontal line, exists on y = m_and_b[1]
        # param is the x value
        return pt_on_line[0]
    elif m_and_b[0] == np.inf:
        # vertical line, exists on x = m_and_b[0]
        # param is the y value
        return pt_on_line[1]
    else:
        # sloped line
        # y = mx + b => x = (y - b) / m
        return (pt_on_line[1] - m_and_b[1]) / (
            m_and_b[0])

def fit_line_to_two_xy(two_xy):
    assert(len(two_xy) == 2)
    f_xy = two_xy[0]
    l_xy = two_xy[1]
    ris = l_xy[1] - f_xy[1]
    run = l_xy[0] - f_xy[0]
    if run == 0: # vertical lines
        return [np.inf, f_xy[0]]
    m = ris / run
    # y = mx + b => b = y - mx
    b = f_xy[1] - m * f_xy[0]
    return [m, b]

def perp_m_and_b(m_and_b, xy):
    if m_and_b[0] == np.inf:
        return [0, xy[1]]
    elif m_and_b[0] == 0:
        return [np.inf, xy[0]]
    perp_m = - 1.0 / m_and_b[0] # important to use float 1.0 for rounding
    # neg reciprocal from 9th grade algebra!
    perp_b = xy[1] - perp_m * xy[0]
    # b = y - mx
    return [perp_m, perp_b]

def two_xy_line_intersect(m_and_b_1, m_and_b_2):
    if m_and_b_1[0] == np.inf and m_and_b_2[0] != np.inf:
        # if 1 is vertical, use its b as x value
        return [m_and_b_1[1],
            m_and_b_2[0] * m_and_b_1[1] + m_and_b_2[1]]
    elif m_and_b_2[0] == np.inf and m_and_b_1[0] != np.inf:
        return [m_and_b_2[1],
            m_and_b_1[0] * m_and_b_2[1] + m_and_b_1[1]]
    elif m_and_b_2[0] == np.inf and m_and_b_1[0] == np.inf:
        # both vertical
        if m_and_b_2[1] == m_and_b_1[1]:
            # colinear
            return [np.inf, m_and_b_1[1]]
        # otherwise no intersection
        return [np.inf, np.inf]
    nom = m_and_b_2[1] - m_and_b_1[1]
    den = m_and_b_1[0] - m_and_b_2[0]
    # print("nom:", nom)
    # print("den", den)
    if abs(den) < 1e-8 and abs(nom) < 1e-8:
        # same line equations
        # print("COLINEAR")
        return [0.0, 0.0]
    if abs(den) < 1e-8:
        # print("den:", den)
        return [0.0, 0.0]
    x = nom / den
    y = m_and_b_1[0] * x + m_and_b_1[1]
    y_2 = m_and_b_2[0] * x + m_and_b_2[1]
    # sometimes y is nan and y_2 is not
    # they should be ideally equal
    final_y = list(filter(lambda x: not math.isnan(x), [y, y_2]))[0]
    return [x, final_y]

def get_pt_param_for_line(m_and_b, pt_on_line):
    if m_and_b[0] < 1e-9:
        # horizontal line, exists on y = m_and_b[1]
        # param is the x value
        return pt_on_line[0]
    elif m_and_b[0] == np.inf:
        # vertical line, exists on x = m_and_b[0]
        # param is the y value
        return pt_on_line[1]
    else:
        # sloped line
        # y = mx + b => x = (y - b) / m
        return (pt_on_line[1] - m_and_b[1]) / (
            m_and_b[0])

def perp_dist_to_line_segment(line_xy_1, line_xy_2, xy):
    pts = [line_xy_1, line_xy_2]
    m_and_b = fit_line_to_two_xy(pts)
    param_1 = get_pt_param_for_line(m_and_b, line_xy_1)
    param_2 = get_pt_param_for_line(m_and_b, line_xy_2)
    sorted_params, param_indices = sort_and_get_indices([param_1, param_2])
    sorted_line_pts = map(lambda x: pts[x], param_indices)

    perp = perp_m_and_b(m_and_b, xy)
    intersection_xy = two_xy_line_intersect(m_and_b,
        perp)

    vec = [
        intersection_xy[0] - xy[0],
        intersection_xy[1] - xy[1]]
    # 2020-09-12:
    # to compare apples-to-apples
    # the 'distance' first return arg
    # will be the distance from xy to intersection_xy
    # whether or not that intersection_xy
    # lies WITHIN the line segment
    # second arg will intersection_xy
    # and third arg will be None if in bounds
    # and the closer bounding point if out bounds

    # this is the main difference:
    # for a line segment, the intersection_xy
    # can exist outside the bounds
    # and if that is the case, get the closer one
    xy_param = get_pt_param_for_line(m_and_b, intersection_xy)
    if xy_param <= sorted_params[0] or xy_param >= sorted_params[1]:
        # out of bounds, get the closer line_pt
        closer_param_dist = abs(xy_param - sorted_params[0])
        closer_line_pt = sorted_line_pts[0]
        if abs(xy_param - sorted_params[1]) < closer_param_dist:
            closer_param_dist = abs(xy_param - sorted_params[1])
            closer_line_pt = sorted_line_pts[1]
        # vec = [
        #     closer_line_pt[0] - intersection_xy[0],
        #     closer_line_pt[1] - intersection_xy[1]]
        # print("out of bounds!",
        #     xy_param,
        #     sorted_params[0],
        #     sorted_params[1],
        #     np.linalg.norm(vec))
        # return -np.inf, intersection_xy
        return np.linalg.norm(vec), intersection_xy, closer_line_pt
    else:
        # vec = [
        #     intersection_xy[0] - xy[0],
        #     intersection_xy[1] - xy[1]]
        # print("in bounds", np.linalg.norm(vec))
        # return -np.inf, intersection_xy
        return np.linalg.norm(vec), intersection_xy, None

def xy_dist_away_along_line(line, line_xy, dist):
    '''
      line: m, b
      line_xy: x, y on line
      dist: scalar along m, b you want to be
    '''
    if np.abs(line_xy[0] * line[0] + line[1] - line_xy[1]) > 1e-8:
        raise Exception("line_xy not on line!")

    delta_x = np.sqrt(dist**2 / (line[0]**2 + 1))

    new_x1 = line_xy[0] + delta_x
    new_xy_1 = [new_x1, line[0]*new_x1 + line[1]]

    new_x2 = line_xy[0] - delta_x
    new_xy_2 = [new_x2, line[0]*new_x2 + line[1]]

    return new_xy_1, new_xy_2

def fast_dist_between_two_xys(list_a, list_b):
    # TODO(j) generalize this and above for n-vec
    x_bit = (list_a[0] - list_b[0]) ** 2
    y_bit = (list_a[1] - list_b[1]) ** 2
    return np.sqrt(x_bit + y_bit)

def prune_elbows(list_of_xys):
    '''
        heuristic, not most efficient / cleanest way
        removes 'triangle' elbows from a list of xys
        walk through every 3 pts a->b->c, if a is closer to c than b, remove b
    '''
    i = 0
    while i+2 < len(list_of_xys):
        dist_a = fast_dist_between_two_xys(list_of_xys[i], list_of_xys[i+1])
        dist_b = fast_dist_between_two_xys(list_of_xys[i], list_of_xys[i+2])
        if dist_b < dist_a:
            # prune i+1 (not most efficient way to do this?)
            list_of_xys = list_of_xys[:i+1] + list_of_xys[i+2:]
        i += 1
    return list_of_xys

def pack_up_for_kml(list_of_globalxys, ah):
    '''
        list_of_globalxys: list, each element is a list[2] of globalx, globaly
    '''
    i = 0
    while i < len(list_of_globalxys):

        site_frame_x, site_frame_y = ah.site_frame_helper.globalframexy_to_siteframexy(
            list_of_globalxys[i][0], list_of_globalxys[i][1])

        lng, lat = ah.site_frame_helper.siteframexy_to_eastingnorthing(
            site_frame_x,
            site_frame_y) 
        z = ah.get_globalframe_height(
            list_of_globalxys[i][0],
            list_of_globalxys[i][1])

        list_of_globalxys[i].append(site_frame_x)
        list_of_globalxys[i].append(site_frame_y)
        list_of_globalxys[i].append(z)
        list_of_globalxys[i].append(lng)
        list_of_globalxys[i].append(lat)
        i+=1
    list_of_dicts = [{
        "lng" : x[-2],
        "lat" : x[-1],
        "x" : x[0],
        "y" : x[1],
        "z" : x[2]
    } for x in list_of_globalxys]
    return list_of_dicts

def main():
    # script deserializes
    parser = argparse.ArgumentParser()
    parser.add_argument("--dem",
        help="dem",
        required=True)
    parser.add_argument("--kml",
        type=str,
        help="kml",
        required=True)
    parser.add_argument("--plot",
        type=str,
        help="plot",
        default="h")

    parser.add_argument("--output_dir",
        help="directory to save files in",
        default="~/Desktop/",
        required=False)
    parser.add_argument("--output_kml_name",
        help="kml name",
        default="site",
        required=False)

    args = parser.parse_args()
    if not os.path.exists(
        os.path.expanduser(args.dem)):
        print("dem not found")

        sys.exit(0)
    if not os.path.exists(
        os.path.expanduser(args.kml)):
        print("kml,not found")
        sys.exit(0)
    kml_path = os.path.expanduser(args.kml)

    doc = open(kml_path, 'rb')
    doc = doc.read()
    print(doc)

    k = kml.KML()
    k.from_string(doc)
    placemarks = k._features[0]._features[0]._features[:-1]
    # last one is linestring of all of them
    lnglats = [[x.geometry.x, x.geometry.y] for x in placemarks]

    site_frame_helper = SiteFrameHelper()
    # dataset = gdal.Open(args.dem)
    # ah = AltitudeHelper(site_frame_helper, dataset)

    '''
    # for quick querying site frame x,y,z
    print site_frame_helper.eastingnorthing_to_siteframexy(
        -47.283886051904972, 87.503357584169123)
    print site_frame_helper.eastingnorthing_to_globalframexy(
            -47.283886051904972, 87.503357584169123)
    print ah.get_eastingnorthing_height(
        -47.283886051904972, 87.503357584169123)
    # -134.03435309086217, 114.98268177984573, 2.101447820663452
    # 5063.72826
    # -13070.27083
    return
    '''

    ##### core algorithm
    original_pts = []

    border_1_lines = []
    border_1_pts = []

    border_2_lines = []
    border_2_pts = []

    margin = [10]*(len(lnglats)-1) # for now margins are all 10
    # for i in range(len(lnglats)-1):
    #     margin[i] = max(10, 40-abs(len(lnglats)/2-i)*10)

    last_border_1_pt = None
    last_border_2_pt = None

    a1s = []
    a2s = []
    b1s = []
    b2s = []

    for i in range(1, len(lnglats)): # for every segment
        # from i-1 to i
        # get line endpoints
        global_xy_a = site_frame_helper.eastingnorthing_to_globalframexy(
            *lnglats[i-1])
        if i == 1:
            original_pts.append(list(global_xy_a))

        global_xy_b = site_frame_helper.eastingnorthing_to_globalframexy(
            *lnglats[i])
        original_pts.append(list(global_xy_b))

        line = fit_line_to_two_xy([global_xy_a, global_xy_b])

        # get line eq, get perp line eq
        perp_line_a = perp_m_and_b(line, global_xy_a)
        perp_line_b = perp_m_and_b(line, global_xy_b)

        # get endpoints shifted by some 'margin' amt
        a1, a2 = xy_dist_away_along_line(
            perp_line_a,
            global_xy_a,
            margin[i-1])

        b1, b2 = xy_dist_away_along_line(
            perp_line_b,
            global_xy_b,
            margin[i-1])

        # shuffle around these
        # such that the as are closer to prior as
        # and a1s are closer to b1s, a2s closer to b2s
        if len(b1s) > 0:
            # currently ordering
            candidate_1 = fast_dist_between_two_xys(b1s[-1], a1)
            candidate_2 = fast_dist_between_two_xys(b2s[-1], a2)
            candidate_3 = fast_dist_between_two_xys(b2s[-1], a1)
            candidate_4 = fast_dist_between_two_xys(b1s[-1], a2)

            if (candidate_1 + candidate_2) > (
                candidate_3 + candidate_4):
                # perform shuffle
                temp = a1
                a1 = a2
                a2 = temp

                # assume that delta algebra / geometry semantics
                # applies to b endpoint as well
                # that it is consistent across line segment (?)
                temp = b1
                b1 = b2
                b2 = temp

        if i == 1:
            border_1_pts.append(a1)
        elif i == len(lnglats)-1:
            last_border_1_pt = b1

        if i == 1:
            border_2_pts.append(a2)
        elif i == len(lnglats)-1:
            last_border_2_pt = b2

        # turn into new line eqs
        if len(a1s) > 0:
            border_1_lines.append(
                fit_line_to_two_xy(
                    [a1s[-1], a1]))

        if len(a2s) > 0:
            border_2_lines.append(
                fit_line_to_two_xy(
                    [a2s[-1], a2]))

        a1s.append(a1)
        a2s.append(a2)
        b1s.append(b1)
        b2s.append(b2)

    # last line segment
    border_1_lines.append(
        fit_line_to_two_xy(
            [a1s[-1], b1s[-1]]))
    border_2_lines.append(
        fit_line_to_two_xy(
            [a2s[-1], b2s[-1]]))

    # get all consecutive line intersection pts
    for i in range(1, len(lnglats)-1):
        # border_1_pts.append(a1s[i])
        # border_1_pts.append(b1s[i])
        # border_2_pts.append(a2s[i])
        # border_2_pts.append(b2s[i])

        border_1_candidate = two_xy_line_intersect(
            border_1_lines[i-1],
            border_1_lines[i])

        border_1_pts.append(border_1_candidate)

        border_2_candidate = two_xy_line_intersect(
            border_2_lines[i-1],
            border_2_lines[i])

        border_2_pts.append(border_2_candidate)

    border_1_pts.append(last_border_1_pt)
    border_2_pts.append(last_border_2_pt)
    ##### core algorithm

    ##### smoothing heuristic: prune elbows
    border_1_pts = prune_elbows(border_1_pts)
    border_2_pts = prune_elbows(border_2_pts)

    ##### produce
    # border_1_list_of_dicts = pack_up_for_kml(border_1_pts, ah)
    # next_kml_name, _ = Util.get_next_valid_name_increment(
    #     os.path.expanduser(args.output_dir),
    #     'border_1',
    #     0,
    #     '',
    #     'kml')
    # kml_str = build_kml_str(
    #     args.output_kml_name + ":border_1",
    #     args.output_kml_name + ":border_1",
    #     [border_1_list_of_dicts],
    #     default_placemark_format="border1-%d")
    # f = open(next_kml_name, "w")
    # f.write(kml_str)
    # f.close()

    # border_2_list_of_dicts = pack_up_for_kml(border_2_pts, ah)
    # next_kml_name, _ = Util.get_next_valid_name_increment(
    #     os.path.expanduser(args.output_dir),
    #     'border_2',
    #     0,
    #     '',
    #     'kml')
    # kml_str = build_kml_str(
    #     args.output_kml_name + ":border_2",
    #     args.output_kml_name + ":border_2",
    #     [border_2_list_of_dicts],
    #     default_placemark_format="border2-%d")
    # f = open(next_kml_name, "w")
    # f.write(kml_str)
    # f.close()

    # all together now
    # original_list_of_dicts = pack_up_for_kml(original_pts, ah)

    # next_kml_name, _ = Util.get_next_valid_name_increment(
    #     os.path.expanduser(args.output_dir),
    #     'combined',
    #     0,
    #     '',
    #     'kml')
    # border_1_list_of_dicts_prefixed = ["border1-%d"] + border_1_list_of_dicts
    # border_2_list_of_dicts_prefixed = ["border2-%d"] + border_2_list_of_dicts
    # kml_str = build_kml_str(
    #     args.output_kml_name + ":combined",
    #     args.output_kml_name + ":combined",
    #     [
    #         original_list_of_dicts,
    #         border_1_list_of_dicts_prefixed,
    #         border_2_list_of_dicts_prefixed
    #     ])
    # f = open(next_kml_name, "w")
    # f.write(kml_str)
    # f.close()

    ##### produce
    colors = 'grcymk'
    f, ax = plt.subplots()
    plt.grid(True)
    plt.gca().set_aspect('equal',
        adjustable='box')
    plt.title("padding a traverse with 2 kmls v1.1")

    plt.plot([x[0] for x in original_pts], [x[1] for x in original_pts], '-o')
    plt.plot([x[0] for x in border_1_pts], [x[1] for x in border_1_pts], '-o')
    plt.plot([x[0] for x in border_2_pts], [x[1] for x in border_2_pts], '-o')

    plt.show()

if __name__ == '__main__':
    main()

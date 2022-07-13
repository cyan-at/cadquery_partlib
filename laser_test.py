import numpy as np

import cadquery as cq

from cq_cam import Job, Profile, METRIC, visualize_task

############################################

result = cq.Workplane("XY")\
    .moveTo(0, 0)\
    .circle(25)\
    .extrude(1.0)
    
result = result.faces(">Z")\
    .circle(15)\
    .cutBlind(-1.0)

job_plane = result.faces('>Z').workplane()
job = Job(job_plane,
          2000, # speed
          2000, # speed
          METRIC,
          0.8) # diameter = laser spot size: 0.8mm

op1 = Profile(job=job,
    o=result.faces('<Z'),
    tool_diameter=1.0,
    face_offset_outer=1,
    face_offset_inner=-1,
    clearance_height=5)
toolpath1 = visualize_task(job, op1, as_edges=True)
result.objects += toolpath1

############################################

'''
result = result.faces(">Z").workplane()\
    .moveTo(0, 6)\
    .rect(3, 3)\
    .cutBlind(-1)

result = result.faces(">Z").workplane()\
    .moveTo(0, -6)\
    .rect(3, 3)\
    .cutBlind(-1)
    
result = result.faces(">Z").workplane()\
    .moveTo(-6, 0)\
    .rect(3, 3)\
    .cutBlind(-1)
    
result = result.faces(">Z").workplane()\
    .moveTo(6, 0)\
    .rect(3, 3)\
    .cutBlind(-1)
'''

############################################

# result =  result.edges("|Z").fillet(1.0)

############################################

'''
op2 = Profile(job=job,
    o=result.faces('<Z'),
    tool_diameter=1.0,
    face_offset_outer=1,
    face_offset_inner=-1,
    clearance_height=5)
toolpath2 = visualize_task(job, op2, as_edges=True)
result.objects += toolpath2
'''

# cq.exporters.export(result,"./%s.dxf" % ("laser_test"))


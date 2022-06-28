import numpy as np

import cadquery as cq

############################################

result = cq.Workplane("XY")\
    .moveTo(0, 0)\
    .circle(9)\
    .extrude(1.0)
    
result = result.faces(">Z")\
    .circle(4)\
    .cutBlind(-1.0)
    
############################################

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
    
############################################

result =  result.edges("|Z").fillet(1.0)

############################################

cq.exporters.export(result,"./%s.dxf" % ("laser_test"))


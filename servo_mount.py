import cadquery as cq

M3 = 3 - 2 * 0.1
M5 = 5 - 2 * 0.1

###########################################################

thickness = 10.0
servo_block_dx = 40.5
servo_block_dy = 20.2
fastener_dx = 49.5
fastener_dy = 10
fastener_dia = M3

mount_diameter = M5

###########################################################

flush_dx = 5
flush_dy = 5
wing_dy = 15 # square

###########################################################

margin_x_l = 10
margin_x_r = 10 + 1.5*flush_dx

margin_y_l = 4
margin_y_r = 4

block_dx = servo_block_dx + margin_x_l + margin_x_r
block_dy = servo_block_dy + margin_y_l + margin_y_r

x_center = margin_x_l + servo_block_dx / 2
y_center = margin_y_l + servo_block_dy / 2

###########################################################

result = cq.Workplane("XY")\
    .moveTo(0, 0)\
    .box(block_dx,
         block_dy,
         thickness,
         centered=False)

result = result.faces(">Z").workplane()\
    .moveTo(x_center, y_center)\
    .rect(servo_block_dx, servo_block_dy)\
    .cutBlind(-thickness)

for dx in [-fastener_dx / 2, fastener_dx / 2]:
    for dy in [-fastener_dy / 2, fastener_dy / 2]:
        x = x_center + dx
        y = y_center + dy
        result = result.faces(">Z").workplane()\
        .pushPoints([[x, y]])\
        .hole(fastener_dia)

###########################################################

########################################## lower y set

# block
result = result.faces("<Y").workplane()\
    .moveTo(thickness / 2, -thickness / 2)\
    .rect(thickness, thickness)\
    .extrude(wing_dy)

# perp
result = result.faces("<X").workplane()\
    .moveTo(wing_dy - thickness / 2, -thickness / 2)\
    .circle(mount_diameter / 2).cutBlind(-thickness)

# face
result = result.faces(">Z").workplane()\
    .moveTo(thickness / 2, -wing_dy + thickness / 2)\
    .circle(mount_diameter / 2).cutBlind(-thickness)

########################################## greater y set

# block
result = result.faces(">Y").workplane()\
    .moveTo(-thickness / 2, -thickness / 2)\
    .rect(thickness, thickness)\
    .extrude(wing_dy)

# perp hole
result = result.faces("<X").workplane()\
    .moveTo(-wing_dy + thickness / 2, -thickness / 2)\
    .circle(mount_diameter / 2).cutBlind(-thickness)

# face hole
result = result.faces(">Z").workplane()\
    .moveTo(thickness / 2, wing_dy - thickness / 2)\
    .circle(mount_diameter / 2).cutBlind(-thickness)

###########################################################

if flush_dx > 0 and flush_dy > 0:    
    result = result.faces(">Z").workplane()\
        .moveTo(block_dx - flush_dx, -flush_dy)\
        .circle(mount_diameter / 2).cutBlind(-thickness)
        
    result = result.faces(">Z").workplane()\
        .moveTo(block_dx - flush_dx, -block_dy + flush_dy)\
        .circle(mount_diameter / 2).cutBlind(-thickness)

###########################################################

result =  result.edges("|Z").fillet(0.5)

cq.exporters.export(result,"./%s.stl" % ("servo_mount"))

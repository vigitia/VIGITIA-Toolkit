# TUIO 2.0 message mapping for VIGITIA (see https://www.vigitia.de/documentation/tuio)
# General concept: messages with the same s_id (session ID) value refer to the same physical entity. If the same object is removed from sensor range and later brought back, it will get a new s_id value.

# c_id (component ID) for tokens and devices refers to a unique ID of that object (e.g. token ID, MAC address)
# c_id for touch points and hands refers to the individual finger (index, ring, thumb, …) or hand (left/right)
# tu_id refers to type/user and can be 0 for now

# empty spaces
#   OCG (outer contour geometry): /tuio2/ocg s_id x_p0 y_p0 ... x_pN y_pN
# every other non-smart object
#   BND (bounding box): /tuio2/bnd s_id x_pos y_pos angle width height area
#   OCG (outer contour geometry): /tuio2/ocg s_id x_p0 y_p0 ... x_pN y_pN
# tokens/fiducials
#   TOK (token): /tuio2/tok s_id tu_id c_id x_pos y_pos angle
# touch points
#   PTR (pointer): /tuio2/ptr s_id tu_id c_id x_pos y_pos angle shear radius press
# hands
#   PTR (pointer): /tuio2/ptr s_id tu_id c_id x_pos y_pos angle shear radius press
#   SKG (skeleton): /tuio2/skg s_id x_p0 y_p0 x_p1 y_p1 node ... x_pN y_pN
# mobile devices
#   TOK (token): /tuio2/tok s_id tu_id c_id x_pos y_pos angle
#   SYM (symbol): /tuio2/sym s_id tu_id c_id group data
# table itself (s_id == 0?)
#   BND (bounding box): /tuio2/bnd s_id x_pos y_pos angle width height area
#   DAT (calibration data): /tuio2/dat s_id mime data


# See TUIO 2.0 Protocól specification (http://www.tuio.org/?tuio20)

# TUIO SERVER

# siehe Referenzimplementierung:
# https://github.com/mkalten/TUIO20_CPP/blob/master/TUIO2/TuioServer.h

# TUIO bundle:
# FRM message:  unique identifier for an individual frame, and therefore has to be included at the beginning of each TUIO bundle






# TUIO Client:

#https://gist.githubusercontent.com/kasperkamperman/3d3d4a8bc921a3298d27/raw/1d23cf2e40e734f42d3497207a50198e3ee3ffeb/oscP5senderReceiver.pde


# Python:
# https://github.com/attwad/python-osc

#Verify manually the if a route exisits (for debug purposes)

import functions as fn
import sumolib
sumo_network_file = 'bari_map.net.xml'
tree, root, coords, junction_ids = fn.load_map(sumo_network_file) 
net = sumolib.net.readNet(sumo_network_file)


from_edge = net.getEdge('-25634153#2')
to_edge = net.getEdge('-25634723')

route = net.getShortestPath(from_edge, to_edge)
if route[0] is None:
    print("No valid route between the edges")
else:
    print(f"Valid route found: {route}")

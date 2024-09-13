import functions as fn
import sumolib
sumo_network_file = 'bari_map.net.xml'
tree, root, coords, junction_ids = fn.load_map(sumo_network_file) 
net = sumolib.net.readNet(sumo_network_file)
from_edge= '-25634153#2'
to_edge= '-25634723'

fn.is_valid_route(from_edge, to_edge, net)

#net.getShortestPath(from_edge, to_edge)
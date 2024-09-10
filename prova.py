#WhiteSheet

import xml.etree.ElementTree as ET
import numpy as np
from sklearn.cluster import KMeans
import matplotlib.pyplot as plt
import sumolib
import csv

## -------------------CONFIGURATION------------------- ##
# Percorso del file di rete SUMO
sumo_network_file = 'massafra_map.net.xml'

# Numero di cluster
num_clusters = 5

# File di output
output_file = 'clustered_map_1.png'
centroids_file = 'centroids_1.csv'
edges_file = 'edges.csv'
border_edges_file = 'border_edges.csv'
all_cluster_border_edges_file = 'all_cluster_border_edges.csv'


#FUNCTIONS FILE

import xml.etree.ElementTree as ET
import numpy as np
from sklearn.cluster import KMeans
import matplotlib.pyplot as plt

# Funzione per caricare la mappa
def load_map(file_path):
    tree = ET.parse(file_path)
    root = tree.getroot()
    junctions = []
    junction_ids = []
    
    for junction in root.findall('.//junction'):
        x = float(junction.get('x'))
        y = float(junction.get('y'))
        junction_ids.append(junction.get('id'))
        junctions.append((x, y))
        
    return tree, root, np.array(junctions), junction_ids

# Funzione per applicare il clustering della mappa
def cluster_junctions(junctions, n_clusters):
    kmeans = KMeans(n_clusters=n_clusters, random_state=0).fit(junctions)
    return kmeans.labels_, kmeans.cluster_centers_

# Funzione per convertire le coordinate SUMO in coordinate geografiche
def convert_to_geographic(centroids, net):
    geographic_coords = []
    for (x, y) in centroids:
        lon, lat = net.convertXY2LonLat(x, y)
        geographic_coords.append((lon, lat))
    return geographic_coords

# Funzione di verifica percorso valido tra due edge
def is_valid_route(from_edge, to_edge, net):
    try:
        route = net.getShortestPath(from_edge, to_edge)
        return route[0] is not None
    except Exception:
        return False

# Funzione per generare i flussi di traffico e salvare ingressi e uscite (per ciascun cluster)
def generate_ingress_egress_per_cluster(edges_by_cluster,junction_clusters, net):
    for cluster_id, edges in edges_by_cluster.items():
        with open(f'traffic_flows_ref/traffic_flows_cluster_{cluster_id}_ref.csv', 'w') as flows_file:
            flow_id = 0
            header = ['FlowID', 'Ingress', 'Egress']
            flows_file.write(','.join(header) + '\n')

            # Estrarre gli edges di ingresso e uscita per ogni cluster cluster
            ingress_edges = []
            egress_edges = []
            for edge in edges:
                from_junction_edges = [e['edge_id'] for e in edges if e['from_junction'] == edge['from_junction']]
                to_junction_edges = [e['edge_id'] for e in edges if e['to_junction'] == edge['to_junction']]
                
                if len(from_junction_edges) == 1:
                    ingress_edges.append(edge)
                if len(to_junction_edges) == 1:
                    egress_edges.append(edge)
            

            # Genera un flusso di traffico per ogni coppia di ingressi e uscite all'interno del cluster
            for ingress in ingress_edges:
                for egress in egress_edges:
                    if ingress != egress:  # Evita che i flussi generati inizino e terminino nello stesso punto
                        ingress_cluster = junction_clusters[ingress['from_junction']]
                        egress_cluster = junction_clusters[egress['to_junction']]
                        
                        # Verifica che ingresso ed uscita di un traffic flow appartengano allo stesso cluster
                        if ingress_cluster == egress_cluster == cluster_id:
                            if is_valid_route(net.getEdge(ingress["edge_id"]), net.getEdge(egress["edge_id"]), net):
                                flow_id_str = f"{cluster_id}_{flow_id}"
                                flows_file.write(f'{flow_id_str},{ingress["edge_id"]},{egress["edge_id"]}\n')
                                flow_id += 1
            

# Funzione per identificare junctions ai margini della mappa
def find_border_junctions(root):
    junction_connections = {}
    for edge in root.findall('.//edge'):
        from_junction = edge.get('from')
        to_junction = edge.get('to')
        if from_junction not in junction_connections:
            junction_connections[from_junction] = 0
        if to_junction not in junction_connections:
            junction_connections[to_junction] = 0
        junction_connections[from_junction] += 1
        junction_connections[to_junction] += 1
    border_junctions = [junction for junction, count in junction_connections.items() if count == 1]
    return border_junctions

# Funzione di plotting della mappa clusterizzata, con border edges evidenziate 
def plot_clusters_and_edges(junctions, labels, edges, centroids, geographic_centroids, border_edges, all_cluster_border_edges, output_file):
    colors = ['red', 'blue', 'green', 'yellow', 'purple', 'orange', 'cyan', 'magenta', 'lime', 'pink']
    plt.figure(figsize=(12, 12))
    
    # Plot junctions
    for i, (x, y) in enumerate(junctions):
        plt.scatter(x, y, color=colors[labels[i] % len(colors)], s=10)
    
    # Plot edges
    for edge in edges:
        x_values = [edge['from'][0], edge['to'][0]]
        y_values = [edge['from'][1], edge['to'][1]]
        from_cluster = edge['from_cluster']
        to_cluster = edge['to_cluster']
        if from_cluster == to_cluster:
            color = colors[from_cluster % len(colors)]
        else:
            color = 'grey'
        plt.plot(x_values, y_values, color=color, linewidth=1)
    
    # Evidenzia border edges (a confine tra un cluster ed un altro)
    for edge in border_edges:
        x_values = [edge['from'][0], edge['to'][0]]
        y_values = [edge['from'][1], edge['to'][1]]
        plt.plot(x_values, y_values, color='black', linewidth=2, linestyle='dashed')
    
    # Evidenzia all cluster border edges (ai margini della mappa)
    for edge in all_cluster_border_edges:
        x_values = [edge['from'][0], edge['to'][0]]
        y_values = [edge['from'][1], edge['to'][1]]
        plt.plot(x_values, y_values, color='orange', linewidth=2, linestyle='dotted')
    
    # Plot centroids
    for i, (x, y) in enumerate(centroids):
        plt.scatter(x, y, color=colors[i % len(colors)], s=100, marker='X', edgecolor='black')
    
    # Legenda 
    legend_labels = [f"Cluster {i}: Lat = {lat:.5f}, Lon = {lon:.5f}" for i, (lon, lat) in enumerate(geographic_centroids)]
    legend_labels.append("Border Edges (between clusters)")
    legend_labels.append("All Cluster Border Edges (on map edge)")
    legend_colors = [plt.Line2D([0], [0], marker='o', color='w', markerfacecolor=colors[i % len(colors)], markersize=10) for i in range(len(geographic_centroids))]
    legend_colors.append(plt.Line2D([0], [0], color='black', linewidth=2, linestyle='dashed'))
    legend_colors.append(plt.Line2D([0], [0], color='orange', linewidth=2, linestyle='dotted'))
    plt.legend(legend_colors, legend_labels, loc='upper right')
    
    plt.title("Clustered Map with Edges and Centroids")
    plt.xlabel("X Coordinate")
    plt.ylabel("Y Coordinate")
    
    plt.savefig(output_file)
    plt.show()


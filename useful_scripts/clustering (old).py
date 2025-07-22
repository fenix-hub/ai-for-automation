import numpy as np
from sklearn.cluster import KMeans
import xml.etree.ElementTree as ET
import matplotlib.pyplot as plt
import sumolib
import csv

# Funzione per caricare e parsare la mappa
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

# Funzione per applicare il clustering
def cluster_junctions(junctions, n_clusters):
    kmeans = KMeans(n_clusters=n_clusters, random_state=0).fit(junctions)
    return kmeans.labels_, kmeans.cluster_centers_

# Funzione per creare la visualizzazione con matplotlib e salvarla come immagine
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
    
    # Highlight border edges
    for edge in border_edges:
        x_values = [edge['from'][0], edge['to'][0]]
        y_values = [edge['from'][1], edge['to'][1]]
        plt.plot(x_values, y_values, color='black', linewidth=2, linestyle='dashed')
    
    # Highlight all cluster border edges
    for edge in all_cluster_border_edges:
        x_values = [edge['from'][0], edge['to'][0]]
        y_values = [edge['from'][1], edge['to'][1]]
        plt.plot(x_values, y_values, color='orange', linewidth=2, linestyle='dotted')
    
    # Plot centroids
    for i, (x, y) in enumerate(centroids):
        plt.scatter(x, y, color=colors[i % len(colors)], s=100, marker='X', edgecolor='black')
    
    # Add legend with geographic coordinates
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
    
    # Salva il plot come immagine
    plt.savefig(output_file)
    plt.show()

# Funzione per convertire le coordinate SUMO in coordinate geografiche
def convert_to_geographic(centroids, net):
    geographic_coords = []
    for (x, y) in centroids:
        lon, lat = net.convertXY2LonLat(x, y)
        geographic_coords.append((lon, lat))
    return geographic_coords

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

# Carica la mappa
file_path = 'massafra_map.net.xml'  # Assicurati di usare il percorso corretto
tree, root, junctions, junction_ids = load_map(file_path)

# Applica il clustering
n_clusters = 5  # Numero di cluster desiderati
labels, centroids = cluster_junctions(junctions, n_clusters)

# Carica la rete SUMO per la conversione delle coordinate
net = sumolib.net.readNet(file_path)

# Extract edges for plotting and identify border edges
edges = []
border_edges = []
for edge in root.findall('.//edge'):
    from_junction = edge.get('from')
    to_junction = edge.get('to')
    if from_junction in junction_ids and to_junction in junction_ids:
        from_coord = tuple(junctions[junction_ids.index(from_junction)])
        to_coord = tuple(junctions[junction_ids.index(to_junction)])
        from_cluster = labels[junction_ids.index(from_junction)]
        to_cluster = labels[junction_ids.index(to_junction)]
        edge_data = {'id': edge.get('id'), 'from': from_coord, 'to': to_coord, 'from_cluster': from_cluster, 'to_cluster': to_cluster}
        edges.append(edge_data)
        if from_cluster != to_cluster:
            border_edges.append(edge_data)

# Converti i centroidi in coordinate geografiche
geographic_centroids = convert_to_geographic(centroids, net)

# Identifica junctions ai margini della mappa
border_junctions = find_border_junctions(root)

# Identifica gli edge con junctions alle coordinate più estreme
extreme_coords_indices = [np.argmin(junctions[:, 0]), np.argmax(junctions[:, 0]), np.argmin(junctions[:, 1]), np.argmax(junctions[:, 1])]
extreme_junction_ids = [junction_ids[idx] for idx in extreme_coords_indices]

# Identifica tutte le junction con un solo collegamento
border_junction_connections = find_border_junctions(root)

# Identifica tutti gli edge ai margini della mappa per ciascun cluster
all_cluster_border_edges = []
for edge in edges:
    from_id = junction_ids[np.where((junctions == edge['from']).all(axis=1))[0][0]]
    to_id = junction_ids[np.where((junctions == edge['to']).all(axis=1))[0][0]]
    if from_id in border_junction_connections or to_id in border_junction_connections:
        all_cluster_border_edges.append(edge)

# Aggiungi gli edge con junctions alle coordinate più estreme (se non già inclusi)
for idx in extreme_coords_indices:
    junction_id = junction_ids[idx]
    for edge in root.findall('.//edge'):
        if edge.get('from') == junction_id or edge.get('to') == junction_id:
            from_junction = edge.get('from')
            to_junction = edge.get('to')
            if from_junction in junction_ids and to_junction in junction_ids:
                from_coord = tuple(junctions[junction_ids.index(from_junction)])
                to_coord = tuple(junctions[junction_ids.index(to_junction)])
                from_cluster = labels[junction_ids.index(from_junction)]
                to_cluster = labels[junction_ids.index(to_junction)]
                edge_data = {'id': edge.get('id'), 'from': from_coord, 'to': to_coord, 'from_cluster': from_cluster, 'to_cluster': to_cluster}
                if edge_data not in all_cluster_border_edges:
                    all_cluster_border_edges.append(edge_data)

# Visualizza la mappa con i cluster, i centroidi, gli edge di frontiera e tutti gli edge ai margini della mappa per ciascun cluster
output_file = 'clustered_map.png'
plot_clusters_and_edges(junctions, labels, edges, centroids, geographic_centroids, border_edges, all_cluster_border_edges, output_file)

# Salva i centroidi in un file CSV
centroids_file = 'centroids.csv'
with open(centroids_file, mode='w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(['Cluster', 'Latitudine', 'Longitudine'])
    for i, (lon, lat) in enumerate(geographic_centroids):
        writer.writerow([i, lat, lon])

# Salva gli edge di frontiera in un file CSV
border_edges_file = 'border_edges.csv'
with open(border_edges_file, mode='w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(['Edge ID', 'From Junction', 'To Junction', 'From Cluster', 'To Cluster', 'From Lat', 'From Lon', 'To Lat', 'To Lon'])
    for edge in border_edges:
        from_id = junction_ids[np.where((junctions == edge['from']).all(axis=1))[0][0]]
        to_id = junction_ids[np.where((junctions == edge['to']).all(axis=1))[0][0]]
        from_lon, from_lat = net.convertXY2LonLat(edge['from'][0], edge['from'][1])
        to_lon, to_lat = net.convertXY2LonLat(edge['to'][0], edge['to'][1])
        writer.writerow([edge['id'], from_id, to_id, edge['from_cluster'], edge['to_cluster'], from_lat, from_lon, to_lat, to_lon])

# Salva tutti gli edge ai margini della mappa per ciascun cluster in un file CSV
all_cluster_border_edges_file = 'all_cluster_border_edges.csv'
with open(all_cluster_border_edges_file, mode='w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(['Edge ID', 'From Junction', 'To Junction', 'From Cluster', 'To Cluster', 'From Lat', 'From Lon', 'To Lat', 'To Lon'])
    for edge in all_cluster_border_edges:
        from_id = junction_ids[np.where((junctions == edge['from']).all(axis=1))[0][0]]
        to_id = junction_ids[np.where((junctions == edge['to']).all(axis=1))[0][0]]
        from_lon, from_lat = net.convertXY2LonLat(edge['from'][0], edge['from'][1])
        to_lon, to_lat = net.convertXY2LonLat(edge['to'][0], edge['to'][1])
        writer.writerow([edge['id'], from_id, to_id, edge['from_cluster'], edge['to_cluster'], from_lat, from_lon, to_lat, to_lon])

print(f"Coordinate geografiche dei centroidi salvate in {centroids_file}")
print(f"Edge di frontiera tra cluster salvati in {border_edges_file}")
print(f"Tutti gli edge ai margini della mappa per ciascun cluster salvati in {all_cluster_border_edges_file}")
print(f"Mappa con cluster e centroidi salvata in {output_file}")

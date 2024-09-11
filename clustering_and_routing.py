import xml.etree.ElementTree as ET
import numpy as np
from sklearn.cluster import KMeans
import matplotlib.pyplot as plt
import sumolib
import csv

## -------------------FUNCTIONS----------------------- ##
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
def generate_traffic_flows_per_cluster(edges_by_cluster, net):
    for cluster_id, edges in edges_by_cluster.items():
        with open(f'traffic_flows_ref/traffic_flows_cluster_{cluster_id}_ref.csv', 'w') as flows_file:
            flow_id = 0
            
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

## -------------------EXECUTION----------------------- ##
# Caricamento file di rete SUMO
sumo_network_file = 'massafra_map.net.xml'
tree, root, coords, junction_ids = load_map(sumo_network_file) 
net = sumolib.net.readNet(sumo_network_file)

# Dati di custering 
num_clusters = 5  # Numero di cluster 
labels, centroids = cluster_junctions(coords, num_clusters)

# Conversione coordinate SUMO - coordinate geografiche dei centoridi
geographic_centroids = convert_to_geographic(centroids, net)

# Assegnazione delle junctions in base al cluster di appartenenza
junction_clusters = {junction_id: labels[i] for i, junction_id in enumerate(junction_ids)}

# Ricerca delle junctions ai margini della mappa
border_junctions = find_border_junctions(root)

# Ricerca degli edges con junctions ai limiti esterni della mappa
extreme_coords_indices = [np.argmin(coords[:, 0]), np.argmax(coords[:, 0]), np.argmin(coords[:, 1]), np.argmax(coords[:, 1])]
extreme_junction_ids = [junction_ids[idx] for idx in extreme_coords_indices]

# Identifica tutte le junction con un solo collegamento (per ipotesi ai limiti della mappa, con una sola connessione)
border_junction_connections = find_border_junctions(root)

# Estrazione dati degli edges che collegano cluster diversi (e degli edges interni ad un cluster)
edges = [] #Vettore di tutti gli edges contenuti nella mappa
border_edges = [] 
for edge in root.findall('.//edge'):
    from_junction = edge.get('from')
    to_junction = edge.get('to')
    if from_junction in junction_ids and to_junction in junction_ids:
        from_coord = tuple(coords[junction_ids.index(from_junction)])
        to_coord = tuple(coords[junction_ids.index(to_junction)])
        from_cluster = labels[junction_ids.index(from_junction)]
        to_cluster = labels[junction_ids.index(to_junction)]
        edge_data = {'id': edge.get('id'), 'from': from_coord, 'to': to_coord, 'from_cluster': from_cluster, 'to_cluster': to_cluster}
        edges.append(edge_data)
        if from_cluster != to_cluster:
            border_edges.append(edge_data)

# Identifica tutti gli edges ai margini della mappa per ciascun cluster
all_cluster_border_edges = []
for edge in edges:
    from_id = junction_ids[np.where((coords == edge['from']).all(axis=1))[0][0]]
    to_id = junction_ids[np.where((coords == edge['to']).all(axis=1))[0][0]]
    if from_id in border_junction_connections or to_id in border_junction_connections:
        all_cluster_border_edges.append(edge)

# Aggiunge gli edges con junctions ai limiti esterni della mappa (se non gia inclusi)
for idx in extreme_coords_indices:
    junction_id = junction_ids[idx]
    for edge in root.findall('.//edge'):
        if edge.get('from') == junction_id or edge.get('to') == junction_id:
            from_junction = edge.get('from')
            to_junction = edge.get('to')
            if from_junction in junction_ids and to_junction in junction_ids:
                from_coord = tuple(coords[junction_ids.index(from_junction)])
                to_coord = tuple(coords[junction_ids.index(to_junction)])
                from_cluster = labels[junction_ids.index(from_junction)]
                to_cluster = labels[junction_ids.index(to_junction)]
                edge_data = {'id': edge.get('id'), 'from': from_coord, 'to': to_coord, 'from_cluster': from_cluster, 'to_cluster': to_cluster}
                if edge_data not in all_cluster_border_edges:
                    all_cluster_border_edges.append(edge_data)


# Estrae gli edges e assegna i cluster
edges_by_cluster = {i: [] for i in range(num_clusters)}
for edge in root.findall('.//edge'):
    if edge.get('function') == 'internal':  # Salta gli edge interni
        continue
    edge_id = edge.get('id')
    from_junction = edge.get('from')
    to_junction = edge.get('to')
    
    if from_junction in junction_clusters and to_junction in junction_clusters:
        from_cluster = junction_clusters[from_junction]
        to_cluster = junction_clusters[to_junction]
        
        # Aggiunge l'edges al cluster se entrambi i punti di giunzione sono nello stesso cluster
        if from_cluster == to_cluster:
            from_coord = convert_to_geographic([coords[junction_ids.index(from_junction)]], net)[0]
            to_coord = convert_to_geographic([coords[junction_ids.index(to_junction)]], net)[0]
            edges_by_cluster[from_cluster].append({
                'edge_id': edge_id,
                'from_junction': from_junction,
                'to_junction': to_junction,
                'from_coord': from_coord,
                'to_coord': to_coord
            })

# Genera i flussi di traffico per ogni cluster
generate_traffic_flows_per_cluster(edges_by_cluster, net)

# Visualizza la mappa con i cluster, i centroidi, gli edge di frontiera e tutti gli edge ai margini della mappa per ciascun cluster
output_file = 'clustered_map.png'
plot_clusters_and_edges(coords, labels, edges, centroids, geographic_centroids, border_edges, all_cluster_border_edges, output_file)

# Salvataggio dei centroidi in un file CSV
centroids_file = 'centroids.csv'
with open(centroids_file, mode='w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(['Cluster', 'Latitudine', 'Longitudine'])
    for i, (lon, lat) in enumerate(geographic_centroids):
        writer.writerow([i, lat, lon])

# Salvataggio di tutti gli edges
edges_file = 'edges.csv'
with open(edges_file, mode='w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(['Edge ID', 'From Junction', 'To Junction', 'From Cluster', 'To Cluster', 'From Lat', 'From Lon', 'To Lat', 'To Lon'])
    for edge in edges:
        from_id = junction_ids[np.where((coords == edge['from']).all(axis=1))[0][0]]
        to_id = junction_ids[np.where((coords == edge['to']).all(axis=1))[0][0]]
        from_lon, from_lat = net.convertXY2LonLat(edge['from'][0], edge['from'][1])
        to_lon, to_lat = net.convertXY2LonLat(edge['to'][0], edge['to'][1])
        writer.writerow([edge['id'], from_id, to_id, edge['from_cluster'], edge['to_cluster'], from_lat, from_lon, to_lat, to_lon])
        
# Salvataggio degli edges di frontiera (interna) in un file CSV
border_edges_file = 'border_edges.csv'
with open(border_edges_file, mode='w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(['Edge ID', 'From Junction', 'To Junction', 'From Cluster', 'To Cluster', 'From Lat', 'From Lon', 'To Lat', 'To Lon'])
    for edge in border_edges:
        from_id = junction_ids[np.where((coords == edge['from']).all(axis=1))[0][0]]
        to_id = junction_ids[np.where((coords == edge['to']).all(axis=1))[0][0]]
        from_lon, from_lat = net.convertXY2LonLat(edge['from'][0], edge['from'][1])
        to_lon, to_lat = net.convertXY2LonLat(edge['to'][0], edge['to'][1])
        writer.writerow([edge['id'], from_id, to_id, edge['from_cluster'], edge['to_cluster'], from_lat, from_lon, to_lat, to_lon])

# Salvataggio di tutti gli edges ai margini della mappa per ciascun cluster in un file CSV
all_cluster_border_edges_file = 'all_cluster_border_edges.csv'
with open(all_cluster_border_edges_file, mode='w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(['Edge ID', 'From Junction', 'To Junction', 'From Cluster', 'To Cluster', 'From Lat', 'From Lon', 'To Lat', 'To Lon'])
    for edge in all_cluster_border_edges:
        from_id = junction_ids[np.where((coords == edge['from']).all(axis=1))[0][0]]
        to_id = junction_ids[np.where((coords == edge['to']).all(axis=1))[0][0]]
        from_lon, from_lat = net.convertXY2LonLat(edge['from'][0], edge['from'][1])
        to_lon, to_lat = net.convertXY2LonLat(edge['to'][0], edge['to'][1])
        writer.writerow([edge['id'], from_id, to_id, edge['from_cluster'], edge['to_cluster'], from_lat, from_lon, to_lat, to_lon])

print("Flussi di traffico generati e salvati in file XML separati per ogni cluster.")
print(f"Coordinate geografiche dei centroidi salvate in {centroids_file}")
print(f"Edge di frontiera tra cluster salvati in {border_edges_file}")
print(f"Tutti gli edge ai margini della mappa per ciascun cluster salvati in {all_cluster_border_edges_file}")
print(f"Mappa con cluster e centroidi salvata in {output_file}")
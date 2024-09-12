import functions as fn
import sumolib
import csv
import numpy as np

# Caricamento file di rete SUMO
sumo_network_file = 'massafra_map.net.xml'
tree, root, coords, junction_ids = fn.load_map(sumo_network_file) 
net = sumolib.net.readNet(sumo_network_file)

# Dati di custering 
num_clusters = 5  # Numero di cluster 
labels, centroids = fn.cluster_junctions(coords, num_clusters)

# Conversione coordinate SUMO - coordinate geografiche dei centoridi
geographic_centroids = fn.convert_to_geographic(centroids, net)

# Assegnazione delle junctions in base al cluster di appartenenza
junction_clusters = {junction_id: labels[i] for i, junction_id in enumerate(junction_ids)}

# Ricerca delle junctions ai margini della mappa
border_junctions = fn.find_border_junctions(root)

# Ricerca degli edges con junctions ai limiti esterni della mappa
extreme_coords_indices = [np.argmin(coords[:, 0]), np.argmax(coords[:, 0]), np.argmin(coords[:, 1]), np.argmax(coords[:, 1])]
extreme_junction_ids = [junction_ids[idx] for idx in extreme_coords_indices]

# Identifica tutte le junction con un solo collegamento (per ipotesi ai limiti della mappa, con una sola connessione)
border_junction_connections = fn.find_border_junctions(root)

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
            from_coord = fn.convert_to_geographic([coords[junction_ids.index(from_junction)]], net)[0]
            to_coord = fn.convert_to_geographic([coords[junction_ids.index(to_junction)]], net)[0]
            edges_by_cluster[from_cluster].append({
                'edge_id': edge_id,
                'from_junction': from_junction,
                'to_junction': to_junction,
                'from_coord': from_coord,
                'to_coord': to_coord
            })

# Genera i flussi di traffico per ogni cluster
fn.generate_ingress_egress_per_cluster(edges_by_cluster,junction_clusters, net)

# Visualizza la mappa con i cluster, i centroidi, gli edge di frontiera e tutti gli edge ai margini della mappa per ciascun cluster
output_file = 'clustered_map.png'
fn.plot_clusters_and_edges(coords, labels, edges, centroids, geographic_centroids, border_edges, all_cluster_border_edges, output_file)

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
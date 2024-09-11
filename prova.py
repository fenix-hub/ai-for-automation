#WhiteSheet
import csv
def get_route_with_edges(from_edge, to_edge, net):
    try:
        # Ottieni il percorso più breve tra due edge
        route = net.getShortestPath(from_edge, to_edge)
        if route[0] is not None:
            # Restituisci solo gli edge intermedi nel percorso
            return route[0]  # route[0] è una lista di edge
        else:
            return None
    except Exception as e:
        print(f"Errore nel calcolare la route da {from_edge.getID()} a {to_edge.getID()}: {str(e)}")
        return None

def get_traffic_volume_from_csv(csv_file, start_coords, end_coords):
    with open(csv_file, mode='r') as file:
        csv_reader = csv.DictReader(file)
        for row in csv_reader:
            if row['start_coords'] == start_coords and row['end_coords'] == end_coords:
                return int(row['vehicles'])  # Restituisce il numero di veicoli dalla colonna 'vehicles'
    return 0  # Valore predefinito se non trovata la rotta

# Funzione per distribuire il traffico sugli edge in base alla lunghezza
def distribute_traffic_along_route(route_edges, total_vehicles):
    total_length = sum(edge.getLength() for edge in route_edges)
    edge_traffic = {}
    for edge in route_edges:
        edge_length = edge.getLength()
        edge_traffic[edge.getID()] = (edge_length / total_length) * total_vehicles
    return edge_traffic

def generate_routes_per_cluster(edges_by_cluster, net):
    routes_data = []
    
    for cluster_id, edges in edges_by_cluster.items():
        ingress_edges = []
        egress_edges = []
        
        # Raccogli ingress e egress edges
        for edge in edges:
            from_junction_edges = [e['edge_id'] for e in edges if e['from_junction'] == edge['from_junction']]
            to_junction_edges = [e['edge_id'] for e in edges if e['to_junction'] == edge['to_junction']]
            
            if len(from_junction_edges) == 1:
                ingress_edges.append(edge)
            if len(to_junction_edges) == 1:
                egress_edges.append(edge)
        
        # Genera rotte per ogni coppia ingress-egress
        for ingress in ingress_edges:
            for egress in egress_edges:
                if ingress != egress:
                    route_edges = get_route_with_edges(net.getEdge(ingress["edge_id"]), net.getEdge(egress["edge_id"]), net)
                    if route_edges:
                        # Salva le informazioni della rotta
                        routes_data.append({
                            'cluster_id': cluster_id,
                            'ingress': ingress,
                            'egress': egress,
                            'route_edges': route_edges,
                            'start_coords': ingress["geo_coords"],
                            'end_coords': egress["geo_coords"]
                        })
    
    return routes_data  # Ritorna le rotte generate per fare richieste TomTom


def write_traffic_flows_from_routes(routes_data, csv_file, net):
    for route in routes_data:
        cluster_id = route['cluster_id']
        ingress = route['ingress']
        egress = route['egress']
        route_edges = route['route_edges']
        start_coords = route['start_coords']
        end_coords = route['end_coords']
        
        # Ottieni il volume di traffico dal CSV
        traffic_volume = get_traffic_volume_from_csv(csv_file, start_coords, end_coords)
        
        if traffic_volume > 0:
            # Distribuisci il traffico sugli edge intermedi
            edge_traffic = distribute_traffic_along_route(route_edges, traffic_volume)
            
            # Scrivi il file dei flussi di traffico
            with open(f'traffic_flows_cluster_{cluster_id}.xml', 'a') as flows_file:
                flow_id_str = f"{cluster_id}_{ingress['edge_id']}_{egress['edge_id']}"
                flows_file.write(f'  <flow id="flow_{flow_id_str}" from="{ingress["edge_id"]}" to="{egress["edge_id"]}" begin="0" end="3600" number="{traffic_volume}"/>\n')

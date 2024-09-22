#THIS SCRIPT CONVERTS EACH ROUTE IN GEO-COORS. AND SAVES RESULTS IN CSVs FOR TOMTOM API CALLS
#All generated files are available in output_flows_coords directory

import xml.etree.ElementTree as ET
import pandas as pd

# Funzione per estrarre gli attributi 'id', 'from', e 'to' dai flussi nel file XML
def extract_flows_from_xml(xml_file_path):
    tree = ET.parse(xml_file_path)
    root = tree.getroot()

    flows = []
    for flow in root.findall('flow'):
        flow_id = flow.get('id')
        from_edge = flow.get('from')
        to_edge = flow.get('to')
        flows.append((flow_id, from_edge, to_edge))

    return flows

# Funzione per ottenere le coordinate geografiche degli edge dal file CSV
def load_edges_coordinates(csv_file_path):
    edges_df = pd.read_csv(csv_file_path)
    edges_dict = edges_df.set_index('Edge ID').to_dict('index')
    return edges_dict

# Funzione per recuperare le coordinate dato un edge ID
def get_coordinates(edge_id, edges_dict):
    if edge_id in edges_dict:
        data = edges_dict[edge_id]
        return {
            "from_lat": data["From Lat"],
            "from_lon": data["From Lon"],
            "to_lat": data["To Lat"],
            "to_lon": data["To Lon"]
        }
    return None

# Generazione CSV di output
def extract_flow_coordinates_for_clusters(number_of_clusters, csv_file_path):
    edges_dict = load_edges_coordinates(csv_file_path)

    for cluster_id in range(0, number_of_clusters):
        xml_file_path = f'traffic_flows_cluster_{cluster_id}.xml'
        output_csv_path = f'output_flows_coords/output_flows_with_coordinates_cluster_{cluster_id}.csv'
        
        flows = extract_flows_from_xml(xml_file_path)
        
        flow_coordinates = []
        for flow_id, from_edge, to_edge in flows:
            from_coords = get_coordinates(from_edge, edges_dict)
            to_coords = get_coordinates(to_edge, edges_dict)
            flow_coordinates.append({
                "flow_id": flow_id,
                # FLOW START
                "start_point_lat": from_coords["from_lat"] if from_coords else None,
                "start_point_lon": from_coords["from_lon"] if from_coords else None,
                
                # FLOW VIA-POINTS
                "via_point_1_lat": from_coords["to_lat"] if from_coords else None,
                "via_point_1_lon": from_coords["to_lon"] if from_coords else None,
                "via_point_2_lat": to_coords["from_lat"] if to_coords else None,
                "via_point_2_lon": to_coords["from_lon"] if to_coords else None,
                
                # FLOW END
                "end_point_lat": to_coords["to_lat"] if to_coords else None,
                "end_point_lon": to_coords["to_lon"] if to_coords else None
            })

        flow_df = pd.DataFrame(flow_coordinates)
        flow_df.to_csv(output_csv_path, index=False)
        print(f"File CSV per il cluster {cluster_id} salvato con successo: {output_csv_path}")


# Esecuzione
csv_file_path = 'edges.csv'
num_clusters=7
extract_flow_coordinates_for_clusters(num_clusters, csv_file_path)

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
def extract_flow_coordinates_to_csv(xml_file_path, csv_file_path, output_csv_path):
    flows = extract_flows_from_xml(xml_file_path)
    edges_dict = load_edges_coordinates(csv_file_path)

    flow_coordinates = []
    for flow_id, from_edge, to_edge in flows:
        from_coords = get_coordinates(from_edge, edges_dict)
        to_coords = get_coordinates(to_edge, edges_dict)
        flow_coordinates.append({
            "flow_id": flow_id,
            #"from_edge": from_edge, #Edge ID
            #FLOW START
            "start_point_lat": from_coords["from_lat"] if from_coords else None,
            "start_point_lon": from_coords["from_lon"] if from_coords else None,
            
            #FLOW VIA-POINTS
            #fine del primo edge (to_lat, to_lon)
            "via_point_1_lat": from_coords["to_lat"] if from_coords else None,
            "via_point_1_lon": from_coords["to_lon"] if from_coords else None,
            #"to_edge": to_edge, #Edge ID
            #inizio del secondo edge (from_lat, from_lon)
            "via_point_2_lat": to_coords["from_lat"] if to_coords else None,
            "via_point_2_lon": to_coords["from_lon"] if to_coords else None,
            
            #FLOW END
            "end_point_lat": to_coords["to_lat"] if to_coords else None,
            "end_point_lon": to_coords["to_lon"] if to_coords else None
        })

    # Convertire i dati in DataFrame e salvarli come CSV
    flow_df = pd.DataFrame(flow_coordinates)
    flow_df.to_csv(output_csv_path, index=False)
    print(f"File CSV salvato con successo: {output_csv_path}")

# Esecuzione del codice
xml_file_path = 'traffic_flows_cluster_1.xml'
csv_file_path = 'edges.csv'
output_csv_path = 'output_flows_with_coordinates.csv'

extract_flow_coordinates_to_csv(xml_file_path, csv_file_path, output_csv_path)

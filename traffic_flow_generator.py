import pandas as pd
import datetime
import os
import json
import xml.etree.ElementTree as ET
import random

# Moduli personali
import tomtom_api
import processor
import csv_handler
import transformer
import curses


L_API_KEY = "pAfBQNn77gp9CKIP4Xa3PqTLwsAMQoT2"
L1_API_KEY = "WVw4DE5L7F9wY6XIT0JCdDn1EIsCuEPt"
L2_API_KEY = "CVchS7iltGcJfPNvkjoeFFwN0hcggJt1"
N_API_KEY = "SdbkkAPVV6GxzS7beuYj8mqYnSRWgUmx"
API_KEY = L1_API_KEY #change when request limit is achived, then set FROM_FLOW_ID to 'auto'
FROM_FLOW_ID = 0 #'auto' #set 0 if are requesting for a new cluster, set 'auto' if you want to add data to existing cluster

FATTORE_SCALA_VEICOLI = 1

# Funzione per generare il file intermedio con le coordinate degli edge di partenza e arrivo
def generate_intermediate(edges_file_path, traffic_flows_ref_path, cluster_id, output_path): 
    csvh = csv_handler.CSVHandler()
    
    # Caricamento dei file CSV
    edges_df = pd.read_csv(edges_file_path)
    traffic_flows_df = pd.read_csv(f'{traffic_flows_ref_path}/traffic_flows_cluster_{cluster_id}_ref.csv')

    # Rinomina delle colonne del file dei flussi di traffico
    traffic_flows_df.columns = ['Flow ID', 'Start Edge ID', 'End Edge ID', 'Flow Length']

    # Unione del file dei flussi con le coordinate degli edge di partenza
    merged_df = traffic_flows_df.merge(edges_df[['Edge ID', 'From Lat', 'From Lon', 'To Lat', 'To Lon']],
                                    how='left',
                                    left_on='Start Edge ID',
                                    right_on='Edge ID').drop(columns='Edge ID')

    # Rinomina delle colonne per chiarezza
    merged_df = merged_df.rename(columns={'From Lat': 'Start From Lat', 'From Lon': 'Start From Lon',
                                        'To Lat': 'Start To Lat', 'To Lon': 'Start To Lon'})

    # Unione del file dei flussi con le coordinate degli edge di arrivo
    merged_df = merged_df.merge(edges_df[['Edge ID', 'From Lat', 'From Lon', 'To Lat', 'To Lon']],
                                how='left',
                                left_on='End Edge ID',
                                right_on='Edge ID').drop(columns='Edge ID')

    # Rinomina delle colonne per chiarezza
    merged_df = merged_df.rename(columns={'From Lat': 'End From Lat', 'From Lon': 'End From Lon',
                                        'To Lat': 'End To Lat', 'To Lon': 'End To Lon'})

    # Salvataggio del file intermedio con le coordinate
    # intermediate_file_path = '/mnt/data/traffic_flows_with_coordinates.csv'
    # merged_df.to_csv(intermediate_file_path, index=False)

    # Step 2: Conteggio delle occorrenze di ogni edge come edge di partenza o di arrivo
    start_counts = traffic_flows_df['Start Edge ID'].value_counts().reset_index()
    start_counts.columns = ['Edge ID', 'Start Count']

    end_counts = traffic_flows_df['End Edge ID'].value_counts().reset_index()
    end_counts.columns = ['Edge ID', 'End Count']


    # genera un valore casuale per ogni riga
    merged_df['Random_const'] = [random.uniform(0.5, 1.0) for _ in range(len(merged_df))]
    merged_df['Gamma'] = 1 / merged_df['Flow Length'] * merged_df['Random_const']

    # normalizza il valore di gamma sommando tutti i gama che condividono lo stesso edge
    merged_df['Gamma_agg'] = merged_df.groupby('Start Edge ID')['Gamma'].transform('sum')
    merged_df['Gamma_norm'] = merged_df['Gamma'] / merged_df['Gamma_agg']

    # Unione dei conteggi degli edge di partenza e di arrivo
    edge_counts_df = pd.merge(start_counts, end_counts, on='Edge ID', how='outer').fillna(0)

    # Salvataggio del file con il conteggio dell'uso degli edge
    # edge_usage_file_path = '/mnt/data/edge_usage_counts.csv'
    # edge_counts_df.to_csv(edge_usage_file_path, index=False)

    """
    # Aggiunta di una colonna ipotetica 'Vehicle Count' con un valore di default
    merged_df['Vehicle Count'] = 100  # Assegniamo un valore predefinito di 100 per simulazione
    """

    # Unione dei conteggi degli edge nel file intermedio
    merged_df = merged_df.merge(edge_counts_df[['Edge ID', 'Start Count']], 
                                left_on='Start Edge ID', right_on='Edge ID', how='left').drop(columns='Edge ID')

    merged_df = merged_df.merge(edge_counts_df[['Edge ID', 'End Count']], 
                                left_on='Start Edge ID', right_on='Edge ID', how='left').drop(columns='Edge ID')

    """
    # Calcolo delle nuove colonne Divided Vehicle Count e Multiplied Vehicle Count
    merged_df['Divided Vehicle Count'] = merged_df['Vehicle Count'] / merged_df['Start Count']
    merged_df['Multiplied Vehicle Count'] = merged_df['Vehicle Count'] * merged_df['End Count']
    """

    # Salvataggio del file aggiornato con le nuove colonne
    csvh.makePath(f'{output_path}/cluster_{cluster_id}')
    updated_intermediate_file_path = f'{output_path}/cluster_{cluster_id}/traffic_flow_data_cluster_{cluster_id}.csv'
    merged_df.to_csv(updated_intermediate_file_path, index=False)

    print(f"File salvato in {updated_intermediate_file_path}")
    return merged_df

# Funzione per ottenere i dati storici di traffico per ogni giorno
def get_historic_data(flows_path, cluster_id, day_range, year, month, slots, output_path, from_flow_id = None ):
    # read the file
    flows_df = pd.read_csv(f'{flows_path}/output_flows_with_coordinates_cluster_{cluster_id}.csv')
    
    # Define a TomTom API Client
    ttapi = tomtom_api.Client(api_key = API_KEY)

    # Define a tomtom processor
    tt_processor = processor.Processor(ttapi)
    historid_csv_handler = csv_handler.CSVHandler()
    
    
    # If from_flow_id is 'auto', start from the last flow_id processed, which is the last folder in {output_path}/cluster_{cluster_id}/historic/flow_{flow_id}
    from_flow_n = from_flow_id
    lstrip = len(f'flow_{cluster_id}_')
    if from_flow_id == 'auto' and os.path.exists(f'{output_path}/cluster_{cluster_id}/historic'):
        flows = next(os.walk(f'{output_path}/cluster_{cluster_id}/historic'))[1]
        sorted_flows = sorted(flows, key=lambda x: int(x.split('_')[-1]))
        for flow in sorted_flows:
            if os.path.exists(f'{output_path}/cluster_{cluster_id}/historic/{flow}'):
                files = next(os.walk(f'{output_path}/cluster_{cluster_id}/historic/{flow}'))[2]
                if len(files) > 0:
                    # get the last date , dates are in format 2024-07-04.csv
                    dates = [f.split('.')[0] for f in files]
                    dates.sort()
                    print (f"Dates: {dates}")
                    last_date = dates[-1]
                    _year, _month, _day = last_date.split('-')
                    if int(_day) < day_range.start:
                        from_flow_id = flow
                        break
            from_flow_id = sorted_flows[-1]
        else:
            from_flow_n = 0
        from_flow_n = int(from_flow_id[lstrip:]) if from_flow_id is not None else 0
        print (f"Starting from flow_id {from_flow_n}")
    
    # Loop per ogni riga nel dataframe e chiamata API
    for index, row in flows_df.iterrows():
        flow_id = row['flow_id']
        
        # Skip tutti i flow già processati
        if from_flow_id is not None and int(flow_id[lstrip:]) < from_flow_n:
            print(f"Skipping flow {flow_id}")
            continue
        
        lat_start = row['start_point_lat']
        lon_start = row['start_point_lon']
        lat_end = row['end_point_lat']
        lon_end = row['end_point_lon']
        via_1_lat = row['via_point_1_lat']
        via_1_lon = row['via_point_1_lon']
        via_2_lat = row['via_point_2_lat']
        via_2_lon = row['via_point_2_lon']
        
        start_point = f"{lat_start},{lon_start}"
        end_point = f"{lat_end},{lon_end}"
        via_points = [f"{via_1_lat},{via_1_lon}", f"{via_2_lat},{via_2_lon}"]
        
        print (f"Processing flow {flow_id}")
        for day in day_range:
            date = datetime.datetime(year, month, day)
            route_summaries = tt_processor.getHistoricDataOnInterval(start_point, end_point, via_points, date, slots, minute_interval=60)
            historid_csv_handler.writeHistoricData(route_summaries, date, f'{output_path}/cluster_{cluster_id}/historic/{flow_id}')
            print(f"Data saved in {output_path}/cluster_{cluster_id}/{flow_id}")
    print ("All data saved")
    return    

# Funzione per ottenere i dati di traffico a partire dai dati storici
def get_traffic_data(traffic_data_path, cluster_id):
    
    trs = transformer.Transformer()
    historid_csv_handler = csv_handler.CSVHandler()
 
    # for each folder in the traffic_data_path
    for flow in os.listdir(f'{traffic_data_path}/cluster_{cluster_id}/historic'):
        # for each csv file in the folder
        for csv in os.listdir(f'{traffic_data_path}/cluster_{cluster_id}/historic/{flow}'):
            datestr = csv.split('.')[0]
            # datetime from filename in format yyyy-mm-dd
            year, month, day = datestr.split('-')
            date = datetime.datetime(int(year), int(month), int(day))
            historic_data = historid_csv_handler.readHistoricData(date, f'{traffic_data_path}/cluster_{cluster_id}/historic/{flow}')
            traffic_data = trs.calculateTrafficData(historic_data)
            historid_csv_handler.writeTrafficData(traffic_data, date, f'{traffic_data_path}/cluster_{cluster_id}/traffic/{flow}')
        print (f"[Get Traffic Data] Flow {flow} data saved")
    print ("[Get Traffic Data] All data saved")


# Funzione per ottenere i dati di traffico slottati
def get_slotted_traffic_data(traffic_data_path, cluster_id, slots):

    trs = transformer.Transformer()
    historid_csv_handler = csv_handler.CSVHandler()
    
    # for each folder in the traffic_data_path
    for flow in os.listdir(f'{traffic_data_path}/cluster_{cluster_id}/traffic'):
        # for each csv file in the folder
        for csv in os.listdir(f'{traffic_data_path}/cluster_{cluster_id}/traffic/{flow}'):
            datestr = csv.split('.')[0]
            # datetime from filename in format yyyy-mm-dd
            year, month, day = datestr.split('-')
            date = datetime.datetime(int(year), int(month), int(day))
            traffic_data = historid_csv_handler.readTrafficData(date, f'{traffic_data_path}/cluster_{cluster_id}/traffic/{flow}')
            slotted_traffic_data = trs.calculateSlottedTraffic(traffic_data, slots)
            historid_csv_handler.writeSlottedTrafficData(slotted_traffic_data, date, f'{traffic_data_path}/cluster_{cluster_id}/slotted_traffic/{flow}')
        print (f"[Get Slotted Traffic Data] Slotted traffic for Flow {flow} data saved")
    print ("[Get Slotted Traffic Data] All data saved")


# Funzione per ottenere i dati di traffico aggregati
def get_aggregated_data(traffic_data_path, cluster_id, slots):
    trs = transformer.Transformer()
    historid_csv_handler = csv_handler.CSVHandler()
    
    # map of flow : aggregated traffic data
    aggregated_traffic_data = {}
    
    # for each csv of each flow in the slotted_traffic_data_path
    for flow in os.listdir(f'{traffic_data_path}/cluster_{cluster_id}/slotted_traffic'):
        # for each csv file in the folder
        combined_data = historid_csv_handler.readAllSlotted(f'{traffic_data_path}/cluster_{cluster_id}/slotted_traffic/{flow}')
        agg = trs.getAggregatedTrafficData(combined_data, slots)
        historid_csv_handler.write(agg, f'{traffic_data_path}/cluster_{cluster_id}/aggregated_traffic/{flow}', 'slotted_traffic_agg.csv')
        
        flow_id = flow.split('flow_')[1]
        # store flow : aggregated traffic data in map
        aggregated_traffic_data[flow_id] = agg
        
        print(f"[Get Aggregated Traffic Data] Aggregated traffic for Flow {flow} data saved")
    
    # Convert DataFrames to dictionaries
    aggregated_traffic_data_dict = {k: v.to_dict() for k, v in aggregated_traffic_data.items()}
    
    # Save to JSON file
    with open(f'{traffic_data_path}/cluster_{cluster_id}/aggregated_traffic_data.json', 'w') as json_file:
        json.dump(aggregated_traffic_data_dict, json_file)
    
    return aggregated_traffic_data


def load_aggregated_data(json_file_path):
    # Load the JSON file
    with open(json_file_path, 'r') as json_file:
        aggregated_traffic_data_dict = json.load(json_file)
    
    # Convert dictionaries back to DataFrames
    aggregated_traffic_data = {k: pd.DataFrame(v) for k, v in aggregated_traffic_data_dict.items()}
    
    return aggregated_traffic_data

# Funzione per generare i file di traffic flow aggregati per tutti i flussi
# @begin_values e @end_values sono i valori di inizio e fine dei flussi per la simulazione su SUMO
def generate_sumo_routes(cluster_id, slot, begin_values = [0, 1800, 5400, 9000], end_values = [3600, 7200, 10800]):
    # Load the CSV file
    df = pd.read_csv(f'traffic_flows_data/cluster_{cluster_id}/traffic_flow_data_cluster_{cluster_id}.csv')

    # Load the JSON file
    with open(f'traffic_flows_data/cluster_{cluster_id}/aggregated_traffic_data.json', 'r') as json_file:
        aggregated_data = json.load(json_file)

    # Create the root element for the XML
    routes = ET.Element('routes')

    # Lista temporanea per raccogliere i flow prima di ordinarli
    flows = []

    # Iterate through each row in the CSV
    for _, row in df.iterrows():
        flow_id = row['Flow ID']
        start_edge_id = row['Start Edge ID']
        end_edge_id = row['End Edge ID']
        start_count = row['Start Count']
        gamma_norm = row['Gamma_norm']
        
        # slot è passato come un time slot in formato hh:mm-hh:mm
        # bisogna trovare l'indice corrispondente nel dizionario aggregato
        slot_index = list(aggregated_data[flow_id]['slot'].keys())[list(aggregated_data[flow_id]['slot'].values()).index(slot)]
        if slot_index is None:
            print(f"Slot {slot} not found in the aggregated data")
            return

        if flow_id in aggregated_data and slot_index in aggregated_data[flow_id]['avg_number_of_vehicles']:
            avg_number_of_vehicles = aggregated_data[flow_id]['avg_number_of_vehicles'][slot_index]
            number_of_vehicles = (avg_number_of_vehicles * gamma_norm) / FATTORE_SCALA_VEICOLI  if start_count != 0 else 0
            number_of_vehicles = round(number_of_vehicles)
            
            while True:
                begin = random.choice(begin_values)
                end = random.choice(end_values)
                if begin < end:
                    break

            # Crea il dizionario del flow con tutti i dettagli
            flow_data = {
                'id': f'flow_{flow_id}',
                'from': start_edge_id,
                'to': end_edge_id,
                'begin': begin,
                'end': end,
                'number': number_of_vehicles
            }
            # Aggiungi il flow alla lista
            flows.append(flow_data)

    # Ordina i flow in base al valore di 'begin'
    flows.sort(key=lambda x: x['begin'])

    # Aggiungi i flow ordinati all'elemento 'routes'
    for flow_data in flows:
        flow = ET.SubElement(routes, 'flow')
        flow.set('id', flow_data['id'])
        flow.set('from', flow_data['from'])
        flow.set('to', flow_data['to'])
        flow.set('begin', str(flow_data['begin']))
        flow.set('end', str(flow_data['end']))
        flow.set('number', str(flow_data['number']))

    # Write the XML to a file
    tree = ET.ElementTree(routes)
    ET.indent(tree)
    fname = f'route_{slot.replace("-","_").replace(":", "-")}'
    tree.write(f'traffic_flows_data/cluster_{cluster_id}/{fname}.xml', encoding='utf-8', xml_declaration=True)

    print(f"Generated traffic flows saved in traffic_flows_data/cluster_{cluster_id}/{fname}.xml")


def reorder_routes(xml_file_path):

    tree = ET.parse(xml_file_path)
    root = tree.getroot()

    # Estre tutti i flow dall'XML
    flows = []
    for flow in root.findall('flow'):
        flow_data = {
            'id': flow.get('id'),
            'from': flow.get('from'),
            'to': flow.get('to'),
            'begin': int(flow.get('begin')),
            'end': int(flow.get('end')),
            'number': flow.get('number')
        }
        flows.append(flow_data)

    # Ordina i flow in base al valore di 'begin'
    flows.sort(key=lambda x: x['begin'])

    # Pulisce l'albero XML dai flow esistenti (disordinati)
    for flow in root.findall('flow'):
        root.remove(flow)

    # Ricompone l'albero con i flow ordinati 
    for flow_data in flows:
        flow = ET.SubElement(root, 'flow')
        flow.set('id', flow_data['id'])
        flow.set('from', flow_data['from'])
        flow.set('to', flow_data['to'])
        flow.set('begin', str(flow_data['begin']))
        flow.set('end', str(flow_data['end']))
        flow.set('number', flow_data['number'])

    # Sovrascrive i file delle routes con i traffic flows ordinati rispetto al begin
    ET.indent(tree)
    tree.write(xml_file_path, encoding='utf-8', xml_declaration=True)


# Define edge file path, traffic flows path, cluster id, and output path
edges_file_path = './edges.csv'
traffic_flows_path = './traffic_flows_ref'
traffic_flow_coords = './output_flows_coords'
output_path = './traffic_flows_data'

POSSIBLE_SLOTS = ["07:00-10:00", "13:00-15:00", "18:00-21:00"]

def select_slots(stdscr):
    curses.curs_set(0)
    stdscr.clear()
    stdscr.refresh()

    selected_slots = [False] * len(POSSIBLE_SLOTS)
    current_selection = 0

    while True:
        stdscr.clear()
        stdscr.addstr(0, 0, "Select time slots using SPACE to toggle and ENTER to confirm:")

        for idx, slot in enumerate(POSSIBLE_SLOTS):
            if selected_slots[idx]:
                stdscr.addstr(idx + 1, 0, f"[X] {slot}")
            else:
                stdscr.addstr(idx + 1, 0, f"[ ] {slot}")

        stdscr.addstr(current_selection + 1, 0, ">")

        key = stdscr.getch()

        if key == curses.KEY_UP and current_selection > 0:
            current_selection -= 1
        elif key == curses.KEY_DOWN and current_selection < len(POSSIBLE_SLOTS) - 1:
            current_selection += 1
        elif key == ord(' '):
            selected_slots[current_selection] = not selected_slots[current_selection]
        elif key == ord('\n'):
            break

    slots = [slot for idx, slot in enumerate(POSSIBLE_SLOTS) if selected_slots[idx]]
    return slots

def select_steps(stdscr):
    curses.curs_set(0)
    stdscr.clear()
    stdscr.refresh()

    steps = [
        "Generate intermediate file with coordinates",
        "Get historic traffic data",
        "Calculate traffic data from historic data",
        "Calculate slotted traffic data",
        "Calculate aggregated traffic data",
        "Generate SUMO routes"
    ]

    selected_steps = [False] * len(steps)
    current_selection = 0

    while True:
        stdscr.clear()
        stdscr.addstr(0, 0, "Select steps to execute using SPACE to toggle and ENTER to confirm:")

        for idx, step in enumerate(steps):
            if selected_steps[idx]:
                stdscr.addstr(idx + 1, 0, f"[X] {step}")
            else:
                stdscr.addstr(idx + 1, 0, f"[ ] {step}")

        stdscr.addstr(current_selection + 1, 0, ">")

        key = stdscr.getch()

        if key == curses.KEY_UP and current_selection > 0:
            current_selection -= 1
        elif key == curses.KEY_DOWN and current_selection < len(steps) - 1:
            current_selection += 1
        elif key == ord(' '):
            selected_steps[current_selection] = not selected_steps[current_selection]
        elif key == ord('\n'):
            break

    return selected_steps

selected_steps = curses.wrapper(select_steps)

execute_steps = {
    "step1": selected_steps[0],
    "step2": selected_steps[1],
    "step3": selected_steps[2],
    "step4": selected_steps[3],
    "step5": selected_steps[4],
    "step6": selected_steps[5]
}

cluster_id = int(input("Enter cluster id: "))

if execute_steps["step2"] or execute_steps["step4"] or execute_steps["step5"] or execute_steps["step6"]:
    slots = curses.wrapper(select_slots)

"""
STEP 1
=====
A partire dai file CSV dei flow, generare un file intermedio con le coordinate degli edge di partenza e arrivo,
nonchè il conteggio degli edge di partenza e arrivo per ogni flow
"""
if execute_steps["step1"]:
    traffic_flow_data_cluster = generate_intermediate(edges_file_path, traffic_flows_path, cluster_id, output_path)

"""
STEP 2
=====
Per ogni flow, chiamare l'API TomTom per ottenere i dati storici di traffico per ogni giorno.
I dati storici vengono salvati in una cartella separata per ogni flow, non serve eseguire nuovamente questa operazione
se i dati sono già stati salvati.
"""
if execute_steps["step2"]:
    # year, month and day range come from terminal input
    year = int(input("Enter the year: "))
    month = int(input("Enter the month: "))
    day_range = range(int(input("Enter the start day: ")), int(input("Enter the end day: ")))    
    get_historic_data(traffic_flow_coords, cluster_id, day_range, year, month, slots, output_path, from_flow_id = FROM_FLOW_ID)

"""
Step 3
=====
Per ogni flow, calcolare i dati di traffico a partire dai dati storici.
"""
if execute_steps["step3"]:
    get_traffic_data(output_path, cluster_id)

"""
STEP 4 
=====
Per ogni flow, calcolare i dati di traffico slottati.
"""
if execute_steps["step4"]:
    get_slotted_traffic_data(output_path, cluster_id, slots)

"""
STEP 5
=====
Per ogni flow, calcolare i dati di traffico aggregati.
"""
if execute_steps["step5"]:
    aggregated_traffic_data_for_flow = get_aggregated_data(output_path, cluster_id, slots)

"""
STEP 6
=====
Generare i file di traffic flow aggregati per tutti i flussi
"""
if execute_steps["step6"]:
    FATTORE_SCALA_VEICOLI = int(input("Enter the vehicle scaling factor for vehicles number (default is 1): ").strip() or 1)
    for slot in slots:
        generate_sumo_routes(cluster_id, slot)
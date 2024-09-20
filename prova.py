# Supponiamo che i valori begin ed end siano questi
begin_values = [0, 600, 1200, 2400]
end_values = [1200, 2400, 3000, 3600]

# Lista temporanea per raccogliere i flow prima di ordinarli
flows = []

for flow_id, slot_data in aggregated_data.items():
    for slot_index, avg_number_of_vehicles in slot_data['avg_number_of_vehicles'].items():
        number_of_vehicles = avg_number_of_vehicles / start_count if start_count != 0 else 0
        
        # Genera i valori pseudorandomici di begin ed end
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
            'number': round(number_of_vehicles)
        }
        # Aggiungi il flow alla lista
        flows.append(flow_data)

# Ordina i flow per il valore di 'begin'
flows.sort(key=lambda x: x['begin'])

# Crea la struttura XML
routes = ET.Element('routes')

# Aggiungi i flow ordinati all'elemento 'routes'
for flow_data in flows:
    flow = ET.SubElement(routes, 'flow')
    flow.set('id', flow_data['id'])
    flow.set('from', flow_data['from'])
    flow.set('to', flow_data['to'])
    flow.set('begin', str(flow_data['begin']))
    flow.set('end', str(flow_data['end']))
    flow.set('number', str(flow_data['number']))

# Scrivi l'XML su un file
tree = ET.ElementTree(routes)
ET.indent(tree)
fname = f'route_{slot.replace("-","_").replace(":", "-")}'
tree.write(f'traffic_flows_data/cluster_{cluster_id}/{fname}.xml', encoding='utf-8', xml_declaration=True)

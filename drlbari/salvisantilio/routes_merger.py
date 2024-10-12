import xml.etree.ElementTree as ET
import os

folder = 'salvisantilio'
sim_end = 10800  # Valore di configurazione per lo shift

def merge_and_sort_route_files(files, output_file):
    all_flows = []

    # Per ogni file XML, estrai i flussi
    for file in files:
        tree = ET.parse(file)
        root = tree.getroot()
        
        for flow in root.findall('flow'):
            all_flows.append(flow)
    
    # Ordina i flussi per l'attributo "begin"
    all_flows.sort(key=lambda x: float(x.get('begin')))
    
    # Crea un nuovo albero XML
    root = ET.Element('routes')
    
    # Aggiungi i flussi ordinati
    for flow in all_flows:
        root.append(flow)
    
    # Replicazione e shift dei flussi con modifica dell'id
    replicate_and_shift_flows(root, all_flows, num_replicas=5, sim_end=sim_end)
    
    # Scrivi il nuovo file XML con la formattazione corretta
    indent_xml(root)
    tree = ET.ElementTree(root)
    tree.write(output_file, encoding='utf-8', xml_declaration=True)

def replicate_and_shift_flows(root, flows, num_replicas, sim_end):
    """
    Replica i flussi esistenti con uno shift nei valori di 'begin' e 'end' e modifica il flow id.
    """
    for i in range(1, num_replicas + 1):
        for flow in flows:
            # Creare una copia del flusso
            new_flow = ET.Element('flow', flow.attrib)
            
            # Modifica il flow id aggiungendo '_idx' dove idx è l'indice corrente
            new_flow.set('id', f"{flow.get('id')}_{i}")
            
            # Aggiorna i valori di 'begin' e 'end' con lo shift
            new_flow.set('begin', str(float(flow.get('begin')) + i * sim_end))
            new_flow.set('end', str(float(flow.get('end')) + i * sim_end))
            
            # Aggiungi la replica al root
            root.append(new_flow)

def indent_xml(elem, level=0):
    """
    Funzione per formattare correttamente l'XML con indentazioni, in linea con lo stile originale.
    """
    i = "\n" + level * "  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for subelem in elem:
            indent_xml(subelem, level + 1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i

# Lista dei file per ogni fascia oraria
files_07_10 = [os.path.join(folder, 'cluster_1/route_07-00_10-00.xml'),
               os.path.join(folder, 'cluster_2/route_07-00_10-00.xml'),
               os.path.join(folder, 'cluster_3/route_07-00_10-00.xml'),
               os.path.join(folder, 'cluster_4/route_07-00_10-00.xml'),
               os.path.join(folder, 'cluster_5/route_07-00_10-00.xml'),
               os.path.join(folder, 'cluster_6/route_07-00_10-00.xml')]

files_13_15 = [os.path.join(folder, 'cluster_1/route_13-00_15-00.xml'),
               os.path.join(folder, 'cluster_2/route_13-00_15-00.xml'),
               os.path.join(folder, 'cluster_3/route_13-00_15-00.xml'),
               os.path.join(folder, 'cluster_4/route_13-00_15-00.xml'),
               os.path.join(folder, 'cluster_5/route_13-00_15-00.xml'),
               os.path.join(folder, 'cluster_6/route_13-00_15-00.xml')]

files_18_21 = [os.path.join(folder, 'cluster_1/route_18-00_21-00.xml'),
               os.path.join(folder, 'cluster_2/route_18-00_21-00.xml'),
               os.path.join(folder, 'cluster_3/route_18-00_21-00.xml'),
               os.path.join(folder, 'cluster_4/route_18-00_21-00.xml'),
               os.path.join(folder, 'cluster_5/route_18-00_21-00.xml'),
               os.path.join(folder, 'cluster_6/route_18-00_21-00.xml')]

# Creazione dei file uniti, ordinati e con replicazione
merge_and_sort_route_files(files_07_10, os.path.join(folder, 'merged_route_07-10.xml'))
merge_and_sort_route_files(files_13_15, os.path.join(folder, 'merged_route_13-15.xml'))
merge_and_sort_route_files(files_18_21, os.path.join(folder, 'merged_route_18-21.xml'))

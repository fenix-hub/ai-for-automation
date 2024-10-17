# Questo script si occupa di creare 3 grandi file di routes, uno per ogni fascia oraria,
# che contengono i flows da runnare in SUMO di ognuno dei clusters. Dal momento che il training dell'agente
# impiega un tempo indefinito di simulazione, vengono generate delle repliche dei flows che consentono a SUMO
# di simulare uno slot temporale di traffico in loop, cosìcchè l'agente esegua il training sulle stesse condizioni
# di traffico in ognuno degli episodi. Le repliche vengono aggiunte per evitare frequenti episodi di reload della simulazione.
# TODO: File unificato con tutte le fasce orarie + Agente con nuova dimensione nello spazio delle osservazioni (id. slot orario)

import xml.etree.ElementTree as ET
import os
import numpy as np

folder = 'drlbari/salvisantilio'
sim_end = 10800  # Valore di configurazione per lo shift
num_replicas = 20 # Numero di repliche dei traffic flows (oltre al primo set di flow)
scale_factor = 6 # Se 1, dati di traffico completi (da evitare)
remove_zeros = True
all_routes_file = True # Se True, crea un unico file di routes con tutte le fasce orarie

def replicate_and_shift_flows(root, flows, num_replicas, sim_end, scale_factor):
    for i in range(1, num_replicas + 1):
        for flow in flows:
            #Crea una copia del flusso
            new_flow = ET.Element('flow', flow.attrib)
            
            #Modifica il flow ID aggiungendo '_idx' dove idx è l'indice corrente di replica
            new_flow.set('id', f"{flow.get('id')}_{i}")
            
            #Aggiorna i valori di 'begin' e 'end' con lo shift
            new_flow.set('begin', str(float(flow.get('begin')) + i * sim_end))
            new_flow.set('end', str(float(flow.get('end')) + i * sim_end))
            
            #Divide l'attributo "number" se esiste per il fattore di scala del traffico
            if 'number' in new_flow.attrib:
                original_number = int(new_flow.get('number'))
                divided_number = str(round(original_number / scale_factor))
                new_flow.set('number', divided_number)
            
            #Aggiunge la replica al root
            root.append(new_flow)

def remove_zero_flows(root):
    #Rimuove tutti gli elementi 'flow' con number=0
    for flow in root.findall('flow'):
        if flow.get('number') == '0':
            root.remove(flow)

#Formattazione dell'xml con aggiunta in coda delle repliche
def indent_xml(elem, level=0):
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


def merge_and_sort_route_files(files, output_file, scale_factor, remove_zeros):
    all_flows = []

    # Legge i flussi dai file
    for file in files:
        tree = ET.parse(file)
        root = tree.getroot()
        
        for flow in root.findall('flow'):
            all_flows.append(flow)

    # Conta il numero di flussi originali
    n_original_flows =  len(all_flows)
    print(f"Numero di flussi originali: {n_original_flows}")
    
    # Ordina i flussi per l'attributo "begin"
    all_flows.sort(key=lambda x: float(x.get('begin')))
    
    root = ET.Element('routes')
    
    # Aggiunge i flussi ordinati all'albero
    for flow in all_flows:
        if 'number' in flow.attrib:
            original_number = int(flow.get('number'))
            divided_number = str(round(original_number / scale_factor))
            flow.set('number', divided_number)
        
        root.append(flow)

    # Replica e shift dei flussi
    replicate_and_shift_flows(root, all_flows, num_replicas, sim_end, scale_factor)
    
    # Rimuove i flussi con number=0, se necessario
    if remove_zeros:
        remove_zero_flows(root)
    
    # Conta il numero di flussi dopo la replicazione
    n_replicated_flows = len(root.findall('flow'))
    print(f"Numero di flussi dopo la replicazione: {n_replicated_flows}")
    
    n=n_original_flows*(1+num_replicas)
    n_removed_flows = str(np.absolute([n-n_replicated_flows]))
    print(f"Totale flow rimossi: {n_removed_flows}")
    # Scrivi il nuovo file XML con la formattazione corretta
    indent_xml(root)
    tree = ET.ElementTree(root)
    tree.write(output_file, encoding='utf-8', xml_declaration=True)


def merge_and_shift_all_route_files(files_07_10, files_13_15, files_18_21, output_file, num_replicas, sim_end, scale_factor, remove_zeros):
    all_flows = []

    # Funzione per aggiungere flussi e applicare uno shift temporale
    def add_shifted_flows(file_list, shift):
        for file in file_list:
            tree = ET.parse(file)
            root = tree.getroot()
            for flow in root.findall('flow'):
                # Applica lo shift ai valori di begin e end
                flow.set('begin', str(float(flow.get('begin')) + shift))
                flow.set('end', str(float(flow.get('end')) + shift))
                all_flows.append(flow)

    # Aggiunge i flussi di ciascuna fascia oraria, con lo shift appropriato
    add_shifted_flows(files_07_10, shift=0)                 # Nessuno shift per 07-10
    add_shifted_flows(files_13_15, shift=sim_end)            # Shift per 13-15
    add_shifted_flows(files_18_21, shift=2 * sim_end)        # Shift per 18-21

    # Ordina tutti i flussi per l'attributo "begin"
    all_flows.sort(key=lambda x: float(x.get('begin')))

    root = ET.Element('routes')

    # Aggiunge i flussi ordinati all'albero
    for flow in all_flows:
        if 'number' in flow.attrib:
            original_number = int(flow.get('number'))
            divided_number = str(round(original_number / scale_factor))
            flow.set('number', divided_number)
        
        root.append(flow)

    # Replica e shift dei flussi
    replicate_and_shift_flows(root, all_flows, num_replicas, sim_end, scale_factor)

    # Rimuove i flussi con number=0, se necessario
    if remove_zeros:
        remove_zero_flows(root)

    # Scrive il nuovo file XML con la formattazione corretta
    indent_xml(root)
    tree = ET.ElementTree(root)
    tree.write(output_file, encoding='utf-8', xml_declaration=True)

#Lista dei file per ogni fascia oraria 
# TODO: rendere automatizzato l'input dei file di route da unificare, poichè num_clusters variabile
files_07_10 = [os.path.join(folder, 'cluster_0/route_07-00_10-00.xml'),
               os.path.join(folder, 'cluster_1/route_07-00_10-00.xml'),
               os.path.join(folder, 'cluster_2/route_07-00_10-00.xml'),
               os.path.join(folder, 'cluster_3/route_07-00_10-00.xml'),
               os.path.join(folder, 'cluster_4/route_07-00_10-00.xml'),
               os.path.join(folder, 'cluster_5/route_07-00_10-00.xml'),
               os.path.join(folder, 'cluster_6/route_07-00_10-00.xml')]

files_13_15 = [os.path.join(folder, 'cluster_0/route_13-00_15-00.xml'),
               os.path.join(folder, 'cluster_1/route_13-00_15-00.xml'),
               os.path.join(folder, 'cluster_2/route_13-00_15-00.xml'),
               os.path.join(folder, 'cluster_3/route_13-00_15-00.xml'),
               os.path.join(folder, 'cluster_4/route_13-00_15-00.xml'),
               os.path.join(folder, 'cluster_5/route_13-00_15-00.xml'),
               os.path.join(folder, 'cluster_6/route_13-00_15-00.xml')]

files_18_21 = [os.path.join(folder, 'cluster_0/route_18-00_21-00.xml'),
               os.path.join(folder, 'cluster_1/route_18-00_21-00.xml'),
               os.path.join(folder, 'cluster_2/route_18-00_21-00.xml'),
               os.path.join(folder, 'cluster_3/route_18-00_21-00.xml'),
               os.path.join(folder, 'cluster_4/route_18-00_21-00.xml'),
               os.path.join(folder, 'cluster_5/route_18-00_21-00.xml'),
               os.path.join(folder, 'cluster_6/route_18-00_21-00.xml')]

if all_routes_file:
    merge_and_shift_all_route_files(files_07_10, files_13_15, files_18_21, 
                                os.path.join(folder, 'merged_all_routes.xml'), 
                                num_replicas, sim_end, scale_factor, remove_zeros)
else:
    # Creazione dei file uniti, ordinati e con repliche
    merge_and_sort_route_files(files_07_10, os.path.join(folder, 'merged_route_07-10.xml'), scale_factor,remove_zeros)
    merge_and_sort_route_files(files_13_15, os.path.join(folder, 'merged_route_13-15.xml'), scale_factor, remove_zeros)
    merge_and_sort_route_files(files_18_21, os.path.join(folder, 'merged_route_18-21.xml'), scale_factor, remove_zeros)

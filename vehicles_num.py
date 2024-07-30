import json
from geopy.distance import geodesic

with open('response.json', 'r') as file:
    data = json.load(file)

coordinates = data["flowSegmentData"]["coordinates"]["coordinate"]

# Funzione per calcolare la lunghezza del segmento
def calcola_lunghezza_segmento(coords):
    lunghezza = 0
    for i in range(len(coords) - 1):
        punto1 = (coords[i]['latitude'], coords[i]['longitude'])
        punto2 = (coords[i+1]['latitude'], coords[i+1]['longitude'])
        lunghezza += geodesic(punto1, punto2).meters
    return lunghezza

# Calcola la lunghezza del segmento
lunghezza_segmento = calcola_lunghezza_segmento(coordinates)
print(f"Lunghezza del segmento: {lunghezza_segmento} metri")

# Estrazione dati di velocità e tempo di viaggio 
current_speed = data["flowSegmentData"]["currentSpeed"]  # in km/h
free_flow_speed = data["flowSegmentData"]["freeFlowSpeed"]  # in km/h
current_travel_time = data["flowSegmentData"]["currentTravelTime"]  # in secondi
free_flow_travel_time = data["flowSegmentData"]["freeFlowTravelTime"]  # in secondi

# Converti le velocità in m/s
current_speed_m_s = current_speed / 3.6
free_flow_speed_m_s = free_flow_speed / 3.6

# Calcola il flusso di traffico (volume di traffico)
# Flusso di traffico = Lunghezza del segmento / Tempo di viaggio
flusso_traffico = lunghezza_segmento / current_travel_time

# Calcola la densità del traffico
# Densità = Flusso di traffico / Velocità corrente
densita_traffico = free_flow_speed_m_s/ flusso_traffico 

# N.B. La densità del traffico è influenzata anche da altri fattori, 
# come condizioni meteo e orari di punta --> modellare un fattore. 

# Calcola il numero stimato di veicoli
# Numero di veicoli = Densità * Lunghezza del segmento
lun_media_veicolo= 4.6;
numero_veicoli = (densita_traffico/lun_media_veicolo) * lunghezza_segmento

print(f"Densità del traffico: {densita_traffico:.2f} veicoli per metro")
print(f"Numero stimato di veicoli: {numero_veicoli:.2f}")
#TomTom API request
#curl "https://api.tomtom.com/traffic/services/4/flowSegmentData/absolute/10/json?key=pAfBQNn77gp9CKIP4Xa3PqTLwsAMQoT2&point=40.59526,17.11481" -o response.json

import folium
import json
#44.52786,11.35211
input_coordinate = {"latitude": 44.52786, "longitude": 11.35211}

# Leggi il file JSON di risposta d TomTom
with open('response1.json', 'r') as file:
    data = json.load(file)

# Coordinate dall'API di TomTom
#coordinates = data["flowSegmentData"]["coordinates"]["coordinate"]
coordinates = data["routes"][0]["legs"][0]["points"]

# Crea una mappa centrata sulla prima coppia di coordinate
mappa = folium.Map(location=[coordinates[0]['latitude'], coordinates[0]['longitude']], zoom_start=14)

# Marker per le coordinate del punto di input con colore diverso
folium.Marker(
    location=[input_coordinate['latitude'], input_coordinate['longitude']],
    icon=folium.Icon(color='red'), 
    popup="Punto di input"  # Testo popup quando si clicca sul marker
).add_to(mappa)

# Punti del segmento stradale alla mappa
#for coord in coordinates:
#   folium.Marker(location=[coord['latitude'], coord['longitude']]).add_to(mappa)

# Linea che collega tutti i punti
linea = folium.PolyLine([(coord['latitude'], coord['longitude']) for coord in coordinates], color="blue", weight=2.5, opacity=1)
linea.add_to(mappa)

# Salva la mappa in un file HTML
mappa.save("mappa.html")

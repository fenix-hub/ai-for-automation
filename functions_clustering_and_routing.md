
| **Funzione**                          | **Descrizione**                                                                                         |
|---------------------------------------|---------------------------------------------------------------------------------------------------------|
| `load_map(file_path)`                 | Carica la mappa da un file XML di rete SUMO. Restituisce l'albero XML, la radice dell'albero, le coordinate delle giunzioni e gli ID delle giunzioni. |
| `cluster_junctions(junctions, n_clusters)` | Applica il clustering KMeans alle giunzioni della mappa. Restituisce le etichette di cluster e i centroidi dei cluster. |
| `convert_to_geographic(centroids, net)` | Converte le coordinate XY dei centroidi in coordinate geografiche (Latitudine e Longitudine) utilizzando la rete SUMO. Restituisce una lista di coordinate geografiche. |
| `is_valid_route(from_edge, to_edge, net)` | Verifica se esiste un percorso valido tra due edge nella rete. Restituisce `True` se esiste un percorso, altrimenti `False`. |
| `generate_traffic_flows_per_cluster(edges_by_cluster, net)` | Genera flussi di traffico per ogni cluster basati sugli ingressi e uscite identificati, e salva questi flussi in file XML separati per ogni cluster. |
| `find_border_junctions(root)`          | Identifica le giunzioni ai margini della mappa, ovvero quelle con solo un collegamento. Restituisce una lista di ID delle giunzioni ai margini. |
| `plot_clusters_and_edges(junctions, labels, edges, centroids, geographic_centroids, border_edges, all_cluster_border_edges, output_file)` | Visualizza la mappa clusterizzata, i centroidi e gli edge di frontiera. Salva la visualizzazione in un file PNG. Evidenzia anche gli edge ai margini della mappa e gli edge di frontiera tra cluster. |

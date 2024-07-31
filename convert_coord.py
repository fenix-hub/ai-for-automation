import sumolib

# Leggi il file della rete
net = sumolib.net.readNet('massafra_map.net.xml')

# Converti le coordinate geografiche in coordinate di rete SUMO
xA, yA = net.convertLonLat2XY(17.11236,40.59245)
xB, yB = net.convertLonLat2XY(17.11207,40.59227)
print(f"Coordinate posA: x={xA}, y={yA}")
print(f"Coordinate posB: x={xB}, y={yB}")

# pick the closest edge
radius = 5
edgesA= net.getNeighboringEdges(xA, yA, radius)
edgesB= net.getNeighboringEdges(xB, yB, radius)

if len(edgesA) > 0:
    distancesAndEdgesA = sorted([(distA, edgeA) for edgeA, distA in edgesA], key=lambda x:x[0])
    distA, closestEdgeA = distancesAndEdgesA[0]
    print(f"L'edge più vicino ad A è {closestEdgeA.getID()} con una distanza di {distA} metri.")

if len(edgesB) > 0:
    distancesAndEdgesB = sorted([(distB, edgeB) for edgeB, distB in edgesB], key=lambda x:x[0])
    distB, closestEdgeB = distancesAndEdgesB[0]
    print(f"L'edge più vicino a B è {closestEdgeB.getID()} con una distanza di {distB} metri.")



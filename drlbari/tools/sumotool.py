import traci.constants as tc
import random
import traci
def addVehicle(traci,ego_idx,current_ego,baseRoute):
	if (ego_idx>-1 and current_ego in traci.vehicle.getIDList()):
		traci.vehicle.unsubscribe(current_ego)
		traci.vehicle.remove(current_ego)
	ego_idx+=1
	current_ego = "EGO_"+str(ego_idx)
	traci.vehicle.add(current_ego,baseRoute)
	traci.vehicle.subscribe(current_ego,(
			tc.VAR_ROUTE_ID,
			tc.VAR_ROAD_ID,
			tc.VAR_POSITION,
			tc.VAR_SPEED,
	))
	return ego_idx,current_ego


def addRandomVehicle(traci,baseRoute,edges):
	random_ego_idx=0
	for idxRandomVehicle in range(0, 20):
		randomEgoRoute = "RANDOM_" + str(random_ego_idx)
		traci.vehicle.add(randomEgoRoute, baseRoute, 'vType_0')
		traci.vehicle.subscribe(randomEgoRoute, (
			tc.VAR_ROUTE_ID,
			tc.VAR_ROAD_ID,
			tc.VAR_POSITION,
			tc.VAR_SPEED,
		))
		findRouteFlag = True
		while findRouteFlag:
			startRandomStreet = ":cluster"
			while ("cluster" in startRandomStreet) or (":" in startRandomStreet):
				startRandomStreet = edges[random.randint(0, len(edges) - 1)]

			endRandomStreet = ":cluster"
			while ("cluster" in endRandomStreet) or (":" in endRandomStreet):
				endRandomStreet = edges[random.randint(0, len(edges) - 1)]

			try:
				stageResult = traci.simulation.findRoute(startRandomStreet, endRandomStreet, "routeByDistance")
				if len(stageResult.edges):
					findRouteFlag = False
			except Exception:
				pass
		traci.vehicle.setRoute(randomEgoRoute, list(stageResult.edges))
		traci.vehicle.setColor(randomEgoRoute, [0, 255, 0])
		random_ego_idx += 1


def numberVehicleCross(sumoNet, traciEnv, edge):
	nextJunction = sumoNet.getEdge(edge).getToNode()._id
	junctionIncoming = sumoNet.getNode(nextJunction).getIncoming()
	junctionOutgoing = sumoNet.getNode(nextJunction).getOutgoing()
	connTraci = traci.getConnection(traciEnv)
	numberVehicleCross = -1
	for itemNode in junctionIncoming:
		nodeName = itemNode._id
		numberVehicleCross += connTraci.edge.getLastStepVehicleNumber(nodeName)
	for itemNode in junctionOutgoing:
		nodeName = itemNode._id
		numberVehicleCross += (connTraci.edge.getLastStepVehicleNumber(nodeName)/0.5)

	return numberVehicleCross
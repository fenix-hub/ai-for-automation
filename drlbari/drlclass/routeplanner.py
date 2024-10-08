import random

import  gymnasium as gym
import traci,sys,os,logging
import traci.constants as tc
import sumolib
import tools.filetools as tools
import drlclass.streetpriority as sp


if 'SUMO_HOME' in os.environ:
	sys.path.append(os.path.join(os.environ['SUMO_HOME'], 'tools'))
else:
	sys.exit("please declare environment variable 'SUMO_HOME'")

# """ Logger """
logger = logging.getLogger(__name__)

# """ sumo binaries and scenario setup """
osPlattform = sys.platform
if str(osPlattform)=="linux":
    sumoBinary = os.path.join(os.environ['SUMO_HOME'], 'bin', 'sumo-gui')
else:
    sumoBinary = os.path.join(os.environ['SUMO_HOME'], 'bin', 'sumo-gui.exe')

#scenario=os.path.join(os.path.dirname(os.getcwd()), "../backupOldFile/scenario5")
#scenario="d:/progetti_ai/drl_train/drlbari/scenario5"
path_parent = os.path.dirname(os.getcwd())

#scenario=os.path.join(os.path.dirname(os.getcwd()),"drlbari", "../backupOldFile/scenario5")


# if str(osPlattform)=="linux":
#     scenario = "/home/parrotola/PycharmProjects/drlbari/scenario5"
#
# else:
#     scenario = "d:/progetti_ai/drl_train/drlbari/scenario5"

scenario = "./scenario5"



sumoCmd = [sumoBinary,"--tls.all-off","-c", os.path.join(scenario, "osm.sumocfg"),"--start"]
sumoNet = sumolib.net.readNet(os.path.join(scenario, "murat_liberta.net.xml"))
baseRoute="r_0"


class Routeplanner(gym.Env):

    #Curve
    REWARD_DISTANCE_LESS = 0.5
    REWARD_DISTANCE_MORE = 0.1
    TRUNCATE_EPISODE_VALUE=150
    REWARD_CURVE = -1
    REWARD_ARRIVING=20

    #Best route
    REWARD_DISTANCE_LESS = 0.5
    REWARD_DISTANCE_MORE = -0.5
    TRUNCATE_EPISODE_VALUE= 50
    REWARD_ARRIVING= 0
    REWARD_CURVE = 0

    #per priority
    #REWARD_ARRIVING= 20
    #REWARD_DISTANCE_LESS = 0.5
    #REWARD_DISTANCE_MORE = -1
    #TRUNCATE_EPISODE_VALUE= 120
    #REWARD_CURVE = 0
    #Curve
    REWARD_DISTANCE_LESS = 1
    REWARD_DISTANCE_MORE = -1.2
    TRUNCATE_EPISODE_VALUE = 150
    #REWARD_CURVE = -1.5
    REWARD_CURVE = -2
    REWARD_ARRIVING=0


    ego_idx = -1
    random_ego_idx=0
    current_ego = "EGO_0"
    edges = []
    prev_dist = 0
    current_road = ""
    prev_road = ""
    reward = 0
    optimalRoute = []
    angleVehiclePrevious=0
    angleVehicleNext=0
    done=False
    startEdge=""
    endEdge=""
    pathRandomIndex=0
    flagPriorityReward=False
    def __init__(self, env_config):

        #self.startEdge = env_config["startEdge"]
        #self.endEdge = env_config["endEdge"]
        self.lstPoint = env_config["lstPoints"]
        self.flagPriorityReward = env_config["flagPriorityReward"]
        pathRandomIndex=random.randint(0, len(self.lstPoint)-1)

        pathRouteFile = os.path.join(env_config["folder"] ,env_config["pathRouteFile"])
        tools.createRouteSumoFile(pathRouteFile, self.startEdge)

        envSumoSimulation = ''.join((random.choice('abcdefghilmnopqrtsxyzpqr') for i in range(7)))
        traci.start(sumoCmd,label=envSumoSimulation)
        self.edges = traci.edge.getIDList()
        self.action_space = gym.spaces.Discrete(2)
        self.observation_space = gym.spaces.Discrete(len(self.edges))

        # aggiungi veicolo
        self.addVehicle()
        self.steps = 0
        self.done=False
    def reset(self,*, seed=None, options=None):
        self.steps = 0
        self.reward=0
        self.done=False
        self.optimalRoute = [self.startEdge]
#        pathRandomIndex=random.randint(0, len(self.lstPoint)-1)
#        self.startEdge=self.lstPoint[pathRandomIndex][0]
#        self.endEdge=self.lstPoint[pathRandomIndex][1]
#        self.addVehicle()
        return self.edges.index(self.startEdge),{}

    def step(self, action):
        self.reward = 0
        self.done = False


        # traci.simulationStep()



        ego_values = traci.vehicle.getSubscriptionResults(self.current_ego)
        self.current_road = ego_values[tc.VAR_ROAD_ID]




        outEdges = {}
        try:
            outEdges = sumoNet.getEdge(self.current_road).getOutgoing()
        except Exception:
            pass

        outEdgesList = []
        for outEdge in outEdges:
            outEdgesList.append(outEdge.getID())

        if len(outEdgesList) > 0:
            if action > len(outEdgesList)-1:

                self.reward = self.reward - 10
                self.done = True
                self.addVehicle()

            else:
                traci.vehicle.setRoute(self.current_ego, [self.current_road, outEdgesList[action]])

                self.prev_road = self.current_road
                self.current_road = outEdgesList[action]
                self.optimalRoute.append(self.prev_road)

                self.addRewardDistance(self.current_road)
                try:
                    self.addRewardAngle(True)
                except:
                    print("********")
                if self.flagPriorityReward:
                    self.addRewardPriorityStreet(self.current_road)


                #print("Velocità max: ",str(traci.vehicle.getMaxSpeed(self.current_ego)))
                #print("Velocità corrente: ", str(traci.vehicle.getSpeed(self.current_ego)))
                edgeInfo=sumoNet.getEdge(self.current_road)
                if edgeInfo._length < 9:
                    traci.vehicle.setSpeed(self.current_ego,0.5)
                simulRoad = self.prev_road
                while simulRoad != self.current_road:
                    traci.simulationStep()

                    ego_values = traci.vehicle.getSubscriptionResults(self.current_ego)
                    if tc.VAR_ROAD_ID in ego_values:
                        simulRoad = ego_values[tc.VAR_ROAD_ID]
                    else:
                        #print("Errori della mappa: ",self.prev_road,"  ",self.current_road)

                        self.reward = self.reward - 10
                        self.done = True
                        self.addVehicle()
                        break
                try:
                    self.addRewardAngle(False)
                except:
                    print("$$$$$4")
                if self.current_road == self.endEdge:
                    self.reward = self.reward + self.REWARD_ARRIVING
                    print("Arrived")
                    #print("ARRIVED: "+str(self.pathRandomIndex))
                    self.done = True
                    self.addVehicle()

#                if self.current_road == self.startEdge:
#                    self.reward = self.reward - 20
#                    observation = self.prev_road
#                    self.done = True


        else:

            self.reward = self.reward - 50
            self.done = True
            self.addVehicle()
        self.steps=self.steps+1
        if self.steps>self.TRUNCATE_EPISODE_VALUE:
            truncate=True
            self.done=True

            self.addVehicle()
        else:
            truncate=False


        return self.edges.index(self.current_road), self.reward, self.done,truncate ,{}

    def addRewardDistance(self, startEdge):
        currentDist = traci.simulation.getDistanceRoad(startEdge, 0, self.endEdge, 0, False)
        if currentDist < self.prev_dist:
            self.reward = self.reward + self.REWARD_DISTANCE_LESS
        else:
            self.reward = self.reward + self.REWARD_DISTANCE_MORE
        self.prev_dist = currentDist
    def addRewardAngle(self,state):
        #angleVehiclePrevious=traci.vehicle.getAngle(self.current_ego)
        if state:
            try:
                self.angleVehiclePrevious = traci.vehicle.getAngle(self.current_ego)
            except:
                print("########")
        else:
            try:
                self.angleVehicleNext = traci.vehicle.getAngle(self.current_ego)
            except:
                print("????????????")

            if abs(self.angleVehicleNext - self.angleVehiclePrevious) > 50:
                self.reward=self.reward+self.REWARD_CURVE

    def addRewardPriorityStreet(self,edge):
        if edge in sp.STREETPRIORITY:
            self.reward = self.reward+sp.STREETPRIORITY[edge]
            #print("Priority")

    def addVehicle(self):
        random_route="r_0"
        self.pathRandomIndex=random.randint(0, len(self.lstPoint)-1)
        self.startEdge=self.lstPoint[self.pathRandomIndex][0]
        self.endEdge=self.lstPoint[self.pathRandomIndex][1]

        if (self.ego_idx > -1 and self.current_ego in traci.vehicle.getIDList()):
            traci.vehicle.unsubscribe(self.current_ego)
            traci.vehicle.remove(self.current_ego)
        #self.random_ego_idx+=1


        self.ego_idx += 1
        self.current_ego = "EGO_" + str(self.ego_idx)
        self.optimalRoute = [self.startEdge]
        traci.vehicle.add(self.current_ego, baseRoute, 'vType_0')
        #traci.vehicle.setRoute(self.current_ego, [self.startEdge, "24884052#0"])
        traci.vehicle.subscribe(self.current_ego, (
            tc.VAR_ROUTE_ID,
            tc.VAR_ROAD_ID,
            tc.VAR_POSITION,
            tc.VAR_SPEED,
        ))
        traci.vehicle.setDecel(self.current_ego,60)
        self.prev_dist = traci.simulation.getDistanceRoad(self.startEdge, 0, self.endEdge, 0, False);
        traci.simulationStep()


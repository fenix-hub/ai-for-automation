import random

import  gymnasium as gym
import traci,sys,os,logging
import traci.constants as tc
import sumolib
import tools.filetools as tools
import drlclass.streetpriority as sp
import drlclass.streettraffic as st

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

class Routeplanner(gym.Env):
    scenario = "<scenario>"

    sumoCmd = []
    sumoNet = None
    baseRoute = "r_0"


    # #Curve
    # REWARD_DISTANCE_LESS = 0.5
    # REWARD_DISTANCE_MORE = 0.1
    # TRUNCATE_EPISODE_VALUE=150
    # REWARD_CURVE = -1
    # REWARD_ARRIVING=20

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
    # REWARD_DISTANCE_LESS = 1
    # REWARD_DISTANCE_MORE = -1
    # TRUNCATE_EPISODE_VALUE=150
    # #REWARD_CURVE = -1.5
    # REWARD_CURVE = -2
    # REWARD_ARRIVING=0


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
    trEnv=traci
    def __init__(self, env_config):

        self.scenario = env_config["folder"]

        self.sumoCmd = [
            sumoBinary,
            "--tls.all-off",
            #"--max-depart-delay", "1000",
            "--ignore-route-errors",
            "--random-depart-offset", "100",
            #"--tls.actuated.jam-threshold", "4",
            #"--time-to-impatience", "20",
            "--ignore-junction-blocker", "10",
            "--scale", "0.05",
            "--human-readable-time", "true",
            #"--delay", "50",
            "-c",
            os.path.join(self.scenario, env_config["pathConfigFile"]),
            "--start",
        ]
        print (self.sumoCmd)
        


        self.sumoNet = sumolib.net.readNet(os.path.join(self.scenario, env_config["pathNetFile"]))
        self.baseRoute = "r_0"

        self.startEdge = env_config["startEdge"]
        self.endEdge = env_config["endEdge"]
        self.lstPoint = env_config["lstPoints"]
        self.flagPriorityReward = env_config["flagPriorityReward"]

        # Write route file
        self.pathRouteFile = os.path.join(env_config["folder"], env_config["pathRouteFile"])
        tools.createRouteSumoFile(self.pathRouteFile, self.startEdge, self.endEdge)

        envSumoSimulation = ''.join((random.choice('abcdefghilmnopqrtsxyzpqr') for i in range(7)))
        #traciEnv=self.trEnv
        self.trEnv.start(self.sumoCmd, label=envSumoSimulation)
        self.edges = self.trEnv.edge.getIDList()

        # OBSERVATION CONFIGURATION
        self.action_space = gym.spaces.Discrete(2)
        self.observation_space = gym.spaces.Discrete(len(self.edges))

        # Observation space includes the road index (discrete) and normalized time (continuous)
        # self.observation_space = gym.spaces.Tuple((
        #    gym.spaces.Discrete(len(self.edges)),  # Road index
        #    gym.spaces.Box(low=0, high=1, shape=(1,))  # Normalized time
        # ))

        # aggiungi veicolo
        self.addVehicle()
        self.steps = 0
        self.done=False

    def reset(self,*, seed=None, options=None):
        self.steps = 0
        self.reward=0
        self.done=False

        #pathRandomIndex=random.randint(0, len(self.lstPoint)-1)
        #self.startEdge=self.lstPoint[pathRandomIndex][0]
        #self.endEdge=self.lstPoint[pathRandomIndex][1]

        self.addVehicle()
        # tools.createRouteSumoFile(self.pathRouteFile, self.startEdge)

        self.optimalRoute = [self.startEdge]
        return self.edges.index(self.startEdge),{}

    def step(self, action):
        self.reward = 0
        self.done = False


        # self.trEnv.simulationStep()



        ego_values = self.trEnv.vehicle.getSubscriptionResults(self.current_ego)
        self.current_road = ego_values[tc.VAR_ROAD_ID]
        
        
        while True:
            try:
                # Verifica se la strada attuale è nella lista edges
                road_index = self.edges.index(self.current_road)
                break  # Esci dal ciclo se trova la strada
            except ValueError:
                # Aspetta il prossimo step della simulazione se la strada non è ancora presente
                print(f"Strada attuale non trovata: {self.current_road}, aspetto...")
                self.trEnv.simulationStep()  # Esegui uno step della simulazione
                # Aggiorna la posizione del veicolo
                ego_values = self.trEnv.vehicle.getSubscriptionResults(self.current_ego)
                self.current_road = ego_values.get(tc.VAR_ROAD_ID, "")




        outEdges = {}
        try:
            outEdges = self.sumoNet.getEdge(self.current_road).getOutgoing()
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
                self.trEnv.vehicle.setRoute(self.current_ego, [self.current_road, outEdgesList[action]])

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

                self.addRewardTraffic(self.current_road)
                #print("Velocità max: ",str(self.trEnv.vehicle.getMaxSpeed(self.current_ego)))
                #print("Velocità corrente: ", str(self.trEnv.vehicle.getSpeed(self.current_ego)))
                edgeInfo = self.sumoNet.getEdge(self.current_road)
                if edgeInfo._length < 9:
                    self.trEnv.vehicle.setSpeed(self.current_ego,0.5)
                simulRoad = self.prev_road
                while simulRoad != self.current_road:
                    self.trEnv.simulationStep()

                    ego_values = self.trEnv.vehicle.getSubscriptionResults(self.current_ego)
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
                    print("Arrivato: ",self.startEdge," ", self.endEdge)
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

        # Add normalized time to the state observation
        normalized_time = self.get_normalized_time()
        
        # print(self.edges)
        print(self.current_road)
        print(self.edges.index(self.current_road))
        road_state = self.edges.index(self.current_road)

        
       


        observation = road_state

        # Combine road state and time as part of the observation
        # observation = (road_state, normalized_time)

        # return observation, self.reward, self.done, truncate, {}

        return self.edges.index(self.current_road), self.reward, self.done,truncate ,{}


    def get_normalized_time(self):
        # Get current simulation time in seconds
        sim_time_ms = self.trEnv.simulation.getCurrentTime()
        sim_time_seconds = sim_time_ms / 1000
    
        # Define time slot (07:00 - 11:00) in seconds
        start_time = 7 * 3600  # 07:00 in seconds
        end_time = 11 * 3600  # 11:00 in seconds
    
        # Normalize current time between 07:00 and 11:00
        normalized_time = (sim_time_seconds - start_time) / (end_time - start_time)
        normalized_time = max(0, min(1, normalized_time))  # Keep the value between 0 and 1
    
        return normalized_time

    def addRewardDistance(self, startEdge):
        currentDist = self.trEnv.simulation.getDistanceRoad(startEdge, 0, self.endEdge, 0, False)
        if currentDist < self.prev_dist:
            self.reward = self.reward + self.REWARD_DISTANCE_LESS
        else:
            self.reward = self.reward + self.REWARD_DISTANCE_MORE
        self.prev_dist = currentDist
    def addRewardAngle(self,state):
        #angleVehiclePrevious=self.trEnv.vehicle.getAngle(self.current_ego)
        if state:
            try:
                self.angleVehiclePrevious = self.trEnv.vehicle.getAngle(self.current_ego)
            except:
                print("########")
        else:
            try:
                self.angleVehicleNext = self.trEnv.vehicle.getAngle(self.current_ego)
            except:
                print("????????????")

            if abs(self.angleVehicleNext - self.angleVehiclePrevious) > 50:
                self.reward=self.reward+self.REWARD_CURVE

    def is_edge_allowed_for_vehicle(self, edge_id):
       
       edge = self.sumoNet.getEdge(edge_id)
       vehicle_type = 'passenger'

       allowed = edge.allows(vehicle_type)
       
       if allowed:
          return True
       
       return False  

    def getRandomRoute(self):
        distanceRandomRoute = 10
        stageResult = []
        while distanceRandomRoute < 1100:
            startRandomStreet = ":cluster"
            while ("cluster" in startRandomStreet) or (":" in startRandomStreet) or not self.is_edge_allowed_for_vehicle(startRandomStreet):
                startRandomStreet = self.edges[random.randint(0, len(self.edges) - 1)]

            endRandomStreet = ":cluster"
            while ("cluster" in endRandomStreet) or (":" in endRandomStreet) or not self.is_edge_allowed_for_vehicle(endRandomStreet):
                endRandomStreet = self.edges[random.randint(0, len(self.edges) - 1)]
            try:
                stageResult = self.trEnv.simulation.findRoute(startRandomStreet, endRandomStreet, "routeByDistance")
                distanceRandomRoute = self.trEnv.simulation.getDistanceRoad(startRandomStreet, 0, endRandomStreet, 0, False)
            except Exception:
                pass

        return startRandomStreet, endRandomStreet

    def addRewardPriorityStreet(self,edge):
        if edge in sp.STREETPRIORITY:
            self.reward = self.reward+sp.STREETPRIORITY[edge]
            #print("Priority")
    def addRewardTraffic(self,edge):
        if edge in st.STREETTRAFFIC:
            self.reward = self.reward+st.STREETTRAFFIC[edge]

    def addVehicle(self):
        random_route="r_0"
        #self.trEnvEnv
        self.startEdge,self.endEdge=self.getRandomRoute()

        if (self.ego_idx > -1 and self.current_ego in self.trEnv.vehicle.getIDList()):
            self.trEnv.vehicle.unsubscribe(self.current_ego)
            self.trEnv.vehicle.remove(self.current_ego)
        #self.random_ego_idx+=1


        self.ego_idx += 1
        self.current_ego = "EGO_" + str(self.ego_idx)
        self.optimalRoute = [self.startEdge]
        self.trEnv.vehicle.add(self.current_ego, self.baseRoute, 'vType_0')

        self.trEnv.vehicle.subscribe(self.current_ego, (
            tc.VAR_ROUTE_ID,
            tc.VAR_ROAD_ID,
            tc.VAR_POSITION,
            tc.VAR_SPEED,
        ))
        self.trEnv.vehicle.setRoute(self.current_ego, [self.startEdge, self.endEdge])
        self.trEnv.vehicle.setDecel(self.current_ego,60)
        self.prev_dist = self.trEnv.simulation.getDistanceRoad(self.startEdge, 0, self.endEdge, 0, False);
        self.trEnv.simulationStep()



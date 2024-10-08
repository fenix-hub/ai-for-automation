import os, sys, logging, ray

from ray.rllib.algorithms import ppo
import matplotlib.pyplot as plt
import drlclass.routeplanner
# import drlclass.routeplannertraffic

sys.setrecursionlimit(100000)

if 'SUMO_HOME' in os.environ:
	sys.path.append(os.path.join(os.environ['SUMO_HOME'], 'tools'))
else:
	sys.exit("please declare environment variable 'SUMO_HOME'")

# """ Logger """
logger = logging.getLogger(__name__)

# """ sumo binaries and scenario setup """
sumoBinary = os.path.join(os.environ['SUMO_HOME'], 'bin', 'sumo-gui.exe')

import shutil
def main ():
	# init directory in which to save checkpoints

	sux="_priority"
	sux="_curve"
	sux="_routing"



	#First case
	startEdge = "29316823#0"
	endEdge = "30029586#4"

	#Second case
	startEdge = "30029586#4"
	endEdge = "29316823#0"

	#First case
	startEdge = "29316823#0"
	endEdge = "30029586#4"

	#NESO
	startEdge="24888729#2"
	endEdge ="-24884068#4"

	#SONE
	startEdge="-24884068#4"
	endEdge ="24888729#2"
	#First case
	startEdge = "29316823#0"
	endEdge = "30029586#4"

	#EO
	startEdge ="29980631#1"
	endEdge ="30029586#5"

	#OE
	startEdge ="30029586#5"
	endEdge ="24888729#1"

	#SN
	startEdge = "50317015#0"
	endEdge = "68576717#3"

	#NS
	startEdge = "68576717#3"
	endEdge = "50317015#0"

	#PULLING
	startEdge = "24884043#0"
	endEdge = "24884196#10"

	chkpt_root = "drl_model_sumo_scenario5"+"_"+ startEdge +"_"+endEdge+sux

	shutil.rmtree(chkpt_root, ignore_errors=True, onerror=None)

	# init directory in which to log results
	ray_results = "{}/ray_results/".format(os.getenv("HOME"))
	shutil.rmtree(ray_results, ignore_errors=True, onerror=None)

	# start Ray -- add `local_mode=True` here for debugging
	ray.init(ignore_reinit_error=True)

	lstPointsRoute = [["24884189#1","29975386#3"],["29975386#3","24884189#1"],["24884189#1","29975386#3"],["29975386#3","24884189#1"],["29975386#3","-29975400#3"]]

	agent = ppo.PPO(env=drlclass.routeplanner.Routeplanner, config={
		"env_config": {"lstPoints":lstPointsRoute, "startEdge":startEdge, "endEdge":endEdge,"flagPriorityReward":False,"folder":"scenario5","pathRouteFile":"example_drl.rou.xml"},
		"num_workers": 0
	})



	status = "{:2d} reward {:6.2f}/{:6.2f}/{:6.2f} len {:4.2f} saved {}"

	i=0
	j=5
	chkpt_file=""
	mean_ppo=[]
	while True:
		result = agent.train()
		i=i+1
		if j==i:
			chkpt_file = agent.save(chkpt_root)
			print("Save Trainset n:",j)
			j=j+5
			break
		print(status.format(
			i + 1,
			result["episode_reward_min"],
			result["episode_reward_mean"],
			result["episode_reward_max"],
			result["episode_len_mean"],
			chkpt_file
		))
		if result["episode_reward_mean"] >=8:
			chkpt_file = agent.save(chkpt_root)
			break
	mean_ppo.append(result['episode_reward_mean'])
	plt.xlabel('Training Episodes', fontsize=22)
	plt.ylabel('Average reward return', fontsize=22)
	plt.title('Avarage reward')
	xs = [x for x in range(len(mean_ppo))]
	plt.plot(xs, mean_ppo)
	plt.show()
	agent.stop()

if __name__ == "__main__":
	main()
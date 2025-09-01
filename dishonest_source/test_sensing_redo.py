from utils import *
from utilsIO import *
from sensing_programs_new_v2 import *
from dishonest_sensing_programs_v2 import *

import numpy as np
from pprint import pprint
import random

from squidasm.run.stack.run import run # type: ignore
from squidasm.sim.stack.common import LogManager # type: ignore

def avg_estimator(prob0: float, i: int):
    arg = min(1, (prob0*2 - 1))
    if i == 0:                     
        est = np.arccos(arg) / num_nodes
    elif i < 3:
        est = ((-1)**i) * np.arccos(arg) / num_nodes + np.pi/2
    else:
        est = -1 * np.arccos(arg) / num_nodes + np.pi

    return est

def avg_estimator_Zflip(prob0: float, i: int):
    arg = min(1, (1 - prob0*2))
    if i == 0:                     
        est = np.arccos(arg) / num_nodes
    elif i < 3:
        est = ((-1)**i) * np.arccos(arg) / num_nodes + np.pi/2
    else:
        est = -1 * np.arccos(arg) / num_nodes + np.pi

    return est

def diff_estimator(prob0: float, i: int, negative: bool = False):
    arg = min(1, (prob0*2 - 1))
    if i == 0:                     
        est = np.arccos(arg)
    elif i < 3:
        est = ((-1)**i) * np.arccos(arg) + 2*np.pi
    else:
        est = -1 * np.arccos(arg) + 4*np.pi

    return (-1)**negative * est

if __name__ == '__main__':
    num_nodes = 4
    ntest = 20
    copies = 21
    f_threshold = 0.1
    num_iters = 100
    network = 'perfect'
    state = "ghz"
    num_dishonest = 1
    dishonest_action = 2    # 0 = no action, 1 = apply phase flip, 2 = apply bit flip
    bitflip_id = 0

    phases = {'Node_1': 0.8491617541132994,
             'Node_2': 0.5274249812999362,
             'Node_3': 2.2709206003197595,
             'Node_4': 1.5548251299811353}

    # Initialize node names
    node_names = [f"Node_{i+1}" for i in range(num_nodes)]
    verifier = node_names[0]
    dishonest_node = node_names[num_nodes-1]
    if bitflip_id != 0 and bitflip_id != num_nodes-1:
        bitflip_node = node_names[bitflip_id]

    # Initialize verifier program
    programs = {verifier: SensingProgram_verifier(verifier, node_names, phases[verifier], ntest, copies, f_threshold)}

    # Initialize dishonest node program
    if dishonest_action == 0:
        programs[dishonest_node] = DishonestSensing_no_action(dishonest_node, node_names, phases[dishonest_node], ntest, copies)
    elif dishonest_action == 1:
        programs[dishonest_node] = DishonestSensing_applyZ(dishonest_node, node_names, phases[dishonest_node], ntest, copies)
    elif dishonest_action == 2:
        programs[dishonest_node] = DishonestSensing_applyX(dishonest_node, node_names, phases[dishonest_node], ntest, copies)
    else:
        raise ValueError("Dishonest action must be either 1 or 2.")
    
    
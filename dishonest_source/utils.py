from pprint import pprint
from typing import List
from verification_programs import *
from verification_programs_v2 import *
from verification_programs_v3 import *
from verification_programs_full import *
from verification_programs_select import *
from plus_state_programs import *
from bell_state_programs import *
from sensing_programs_new_v2 import *
from dishonest_verif_programs import *
from dishonest_sensing_programs_v2 import *

from netsquid_netbuilder.modules.clinks import DefaultCLinkConfig
from netsquid_netbuilder.modules.qlinks import DepolariseQLinkConfig
from netsquid_netbuilder.modules.qdevices import GenericQDeviceConfig
from netsquid_netbuilder.modules.qlinks.perfect import PerfectQLinkConfig

from squidasm.util.util import create_complete_graph_network # type: ignore
import random
import numpy as np
from collections import deque
pwd = '/home/pgnair/stage/dishonest_source'

###
#   Function to initialize GHZ verification programs on all nodes in the network
#   Initializes one of two versions of the verification protocol
#   Automatically selects the first node as the Verifier
#   Also returns a list of node names for the network
###
def init_verification_programs(num_nodes: int, n_test: int, select: int=0, full: bool=False, version: int=2, state: str="ghz"):

    # Initialize node names list and select verifier node
    node_names = [f"Node_{i+1}" for i in range(num_nodes)]
    verifier = node_names[0]

    if select > 0:
        programs = {verifier: GHZVerifierNode_select(verifier, node_names, n_test, select)}
        programs.update({name: GHZMemberNode_select(name, node_names, n_test, select) 
                                for name in node_names if name != verifier})
    
    elif full:
        programs = {verifier: GHZVerifierNode_full(verifier, node_names, n_test)}
        programs.update({name: GHZMemberNode_full(name, node_names, n_test) 
                                for name in node_names if name != verifier})

    elif version == 1:
        programs = {verifier: GHZProgram_verifier(verifier, node_names, n_test)}
        programs.update({name: GHZProgram_member(name, node_names, n_test) 
                        for name in node_names if name != verifier})
    
    elif version == 2:
        if state == "ghz":
            programs = {verifier: GHZVerifierNode_v2(verifier, node_names, n_test)}
            programs.update({name: GHZMemberNode_v2(name, node_names, n_test) 
                            for name in node_names if name != verifier})
        elif state == "plus":
            programs = {verifier: GHZVerifier_plus_states(verifier, node_names, n_test)}
            programs.update({name: GHZMember_plus_states(name, node_names, n_test) 
                            for name in node_names if name != verifier})
        elif state == "bell":
            if num_nodes % 2 != 0:
                raise ValueError("In order to run bell state programs, num_nodes must be an even number.")
            programs = {verifier: GHZVerifier_bell_states(verifier, node_names, n_test)}
            programs.update({name: GHZMember_bell_states(name, node_names, n_test) 
                            for name in node_names if name != verifier})
        else:
            raise ValueError("State must be one of 'ghz', 'plus', or 'bell'.")
    elif version == 3:
        if state == "ghz":
            programs = {verifier: GHZVerifierNode_v3(verifier, node_names, n_test)}
            programs.update({name: GHZMemberNode_v3(name, node_names, n_test) 
                            for name in node_names if name != verifier})
        else:
            raise ValueError("Version 3 is only compatible with GHZ states.")
    else:
        raise ValueError("Protocol version number must be 1, 2 or 3.")

    return programs, node_names

def init_new_verification(num_nodes: int, n_test: int, copies: int):
    # Initialize node names list and select verifier node
    node_names = [f"Node_{i+1}" for i in range(num_nodes)]
    verifier = node_names[0]

    programs = {verifier: GHZVerifierNode_new(verifier, node_names, n_test, copies)}
    programs.update({name: GHZMemberNode_new(name, node_names, n_test, copies) 
                            for name in node_names if name != verifier})
    
    return programs, node_names

def init_dishonest_verification(num_nodes: int, n_test: int, copies: int, num_dishonest: int, action: int):
    # Initialize node names list and select verifier node
    node_names = [f"Node_{i+1}" for i in range(num_nodes)]
    verifier = node_names[0]

    if num_dishonest not in range(1, num_nodes):
        raise ValueError("Number of dishonest parties must be between 1 and n-1.")

    # Assign verifier program to first node
    programs = {verifier: GHZVerifierNode_new(verifier, node_names, n_test, copies)}

    dishonest_nodes = random.sample(node_names[1:], num_dishonest)

    programs.update({name: GHZMemberNode_new(name, node_names, n_test, copies) 
                    for name in node_names if name != verifier and name not in dishonest_nodes})
    
    if action == 1:
        programs.update({name: DishonestNode_applyZ(name, node_names, n_test, copies) 
                         for name in dishonest_nodes})
    elif action == 2:
        programs.update({name: DishonestNode_applyX(name, node_names, n_test, copies) 
                         for name in dishonest_nodes})
    else:
        raise ValueError("Dishonest action must be either 1 or 2.")
    
    return programs, node_names, dishonest_nodes


def init_sensing_programs(num_nodes: int, n_test: int, copies: int, failure_threshold: float):
    # Initialize node names list and select verifier node
    node_names = [f"Node_{i+1}" for i in range(num_nodes)]
    verifier = node_names[0]

    # Randomly assign local phases to each node
    phases = {}
    for name in node_names:
        phases[name] = random.uniform(0, np.pi)

    programs = {verifier: SensingProgram_verifier(verifier, node_names, phases[verifier], n_test, copies, failure_threshold)}
    programs.update({name: SensingProgram_member(name, node_names, phases[name], n_test, copies) 
                    for name in node_names if name != verifier})
    
    return programs, node_names, phases

def init_dishonest_sensing(num_nodes: int, n_test: int, copies: int, failure_threshold: float, num_dishonest: int, action: int, bitflip_node: int=0):
    # Input validation
    if num_dishonest not in range(1, num_nodes):
        raise ValueError("Number of dishonest parties must be between 1 and n-1.")
    
    # Initialize node names list and select verifier node
    node_names = [f"Node_{i+1}" for i in range(num_nodes)]
    verifier = node_names[0]
    
    # Randomly assign local phases to each node
    phases = {}
    for name in node_names:
        phases[name] = random.uniform(0, np.pi)

    # Assign verifier program to first node
    programs = {verifier: SensingProgram_verifier(verifier, node_names, phases[verifier], n_test, copies, failure_threshold)}

    # Randomly select dishonest nodes
    dishonest_nodes = random.sample(node_names[1:], num_dishonest)

    # Identify node with a bit flip error and ensure it is honest
    bitflip_name = node_names[bitflip_node]
    if bitflip_name in dishonest_nodes:
        raise ValueError(f"Bit flip must be applied to one of the honest nodes.")
    
    # Initialize bit flip program unless it is verifier
    if bitflip_name != verifier:
        programs[bitflip_name] = SensingProgram_member_bitflip(bitflip_name, node_names, phases[bitflip_name], n_test, copies)

    # Initialize dishonest programs
    if action == 0:
        programs.update({name: DishonestSensing_no_action(name, node_names, phases[name], n_test, copies) 
                         for name in dishonest_nodes})
    elif action == 1:
        programs.update({name: DishonestSensing_applyZ(name, node_names, phases[name], n_test, copies) 
                         for name in dishonest_nodes})
    elif action == 2:
        programs.update({name: DishonestSensing_applyX(name, node_names, phases[name], n_test, copies) 
                         for name in dishonest_nodes})
    else:
        raise ValueError("Dishonest action must be either 1 or 2.")
        
    # Initialize standard member programs for remaining nodes
    programs.update({name: SensingProgram_member(name, node_names, phases[name], n_test, copies) 
                    for name in node_names if name not in programs})
    
    return programs, node_names, dishonest_nodes, phases

def init_dishonest_sensing_given(node_names: List[str], n_test: int, copies: int, failure_threshold: float, dishonest_node: int, bitflip_node: int, phases: Dict[str, float]):   
    # Assign verifier program to first node
    verifier = node_names[0]
    programs = {verifier: SensingProgram_verifier(verifier, node_names, phases[verifier], n_test, copies, failure_threshold)}

    # Identify dishonest node and ensure it is not the verifier
    dishonest_name = node_names[dishonest_node]
    if verifier == dishonest_name:
        raise ValueError(f"Verifier node cannot be dishonest.")

    # Identify node with a bit flip error and ensure it is honest and not the verifier
    bitflip_name = node_names[bitflip_node]
    if bitflip_name == dishonest_name:
        raise ValueError(f"Bit flip must be applied to one of the honest nodes.")
    elif bitflip_name == verifier:
        raise ValueError(f"Bit flip cannot be applied to the verifier node.")
    
    # Initialize bit flip program
    programs[bitflip_name] = SensingProgram_member_bitflip(bitflip_name, node_names, phases[bitflip_name], n_test, copies)

    # Initialize dishonest program
    programs[dishonest_name] = DishonestSensing_no_action(dishonest_name, node_names, phases[dishonest_name], n_test, copies)
        
    # Initialize standard member programs for remaining nodes
    programs.update({name: SensingProgram_member(name, node_names, phases[name], n_test, copies) 
                    for name in node_names if name not in programs})
    
    return programs

###
#   Function to load configuration for a generic qdevice from YAML file.
#   Files should be in folder named 'qia_params' in the working directory.
#   Files must be named qdevice_params{_current, _optimistic}.yaml
###
def configure_qdevice(use_optimistic: bool=False, is_perfect: bool=False, num_qubits: int=100):
    if is_perfect:
        # Generate generic qdevice configuration with no noise
        qdevice_cfg = GenericQDeviceConfig.perfect_config(num_qubits)
    else:
        postfix = "_optimistic" if use_optimistic else "_current"
        # Load generic qdevice configuration from YAML file
        qdevice_cfg = GenericQDeviceConfig.from_file(f"{pwd}/qia_params/qdevice_params{postfix}.yaml")
        qdevice_cfg.num_qubits = num_qubits

    return qdevice_cfg

###
#   Function to load configuration for a quantum link from YAML file.
#   Link type must be either 'perfect' or 'depolarise'. 
#   If not specified, 'depolarise' configuration will be created by default.
#   Files should be in folder named 'qia_params' in the working directory.
#   Files must be named link_params{_current, _optimistic}{_high_fid}.yaml
###
def configure_link(use_high_fidelity: bool=False, use_optimistic: bool=False, link_typ: str="depolarise"):
    if link_typ == "perfect":
        # Generate perfect link configuration
        link_cfg = DepolariseQLinkConfig.from_file(f"{pwd}/qia_params/link_params_perfect.yaml")
    else:
        postfix = "_optimistic" if use_optimistic else "_current"
        if use_high_fidelity:
            postfix += "_high_fid" 
        # Load link configuration based on link type requested
        if link_typ == "depolarise":
            link_cfg = DepolariseQLinkConfig.from_file(f"{pwd}/qia_params/link_params{postfix}.yaml")
        else:
            raise ValueError("Unsupported link type")
    
    return link_cfg


### 
#   Function to configure network given the node names, quantum link type, and parameter options.
#   Uses configure_device and configure_link to generate stack and link configurations.
#   Link type is 'depolarise' by default
#   Generates a clink configuration based on 50 km separation and speed of light of 200,000 km/s.
#   Returns StackNetworkConfig object generated by create_complete_graph_network function
###
def configure_network(node_names: List[str], use_high_fidelity: bool, use_optimistic: bool, link_typ: str='depolarise'):
    # Load generic qdevice configuration from YAML file
    qdevice_cfg = configure_qdevice(use_optimistic)
    # Create clink configuration 
    clink_cfg = DefaultCLinkConfig(speed_of_light=200_000, length=50)
    # Load link configuration based on link type requested
    link_cfg = configure_link(use_high_fidelity, use_optimistic, link_typ)
    
    # Create network configuration based on given parameters
    network_cfg = create_complete_graph_network(
            node_names,
            link_typ=link_typ,
            link_cfg=link_cfg,
            clink_typ="default",
            clink_cfg=clink_cfg,
            qdevice_typ="generic",
            qdevice_cfg=qdevice_cfg
        )

    return network_cfg

###
#   Function to generate configuration for a noiseless network.
#   Uses configure_qdevice to generate generic qdevice config with no noise.
#   Generates default link and clink config with 100 ns delay
###
def configure_perfect_network(node_names: List[str]):
    # Generate generic qdevice config with no noise
    qdevice_cfg = configure_qdevice(is_perfect=True)
    # Create clink configuration 
    clink_cfg = DefaultCLinkConfig(delay=100)
    # Generate perfect link configuration
    link_cfg = PerfectQLinkConfig(state_delay=100)

    # Create network configuration based on given parameters
    network_cfg = create_complete_graph_network(
            node_names,
            link_typ="perfect",
            link_cfg=link_cfg,
            clink_typ="default",
            clink_cfg=clink_cfg,
            qdevice_typ="generic",
            qdevice_cfg=qdevice_cfg
        )
    
    return network_cfg  
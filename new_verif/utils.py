from pprint import pprint
from typing import List
from verification_programs import *
from verification_programs_v2 import *
from verification_programs_v3 import *
from verification_programs_full import *
from verification_programs_select import GHZVerifierNode_select, GHZMemberNode_select
from plus_state_programs import *
from bell_state_programs import *
from sensing_programs_new import *

from netsquid_netbuilder.modules.clinks import DefaultCLinkConfig
from netsquid_netbuilder.modules.qlinks import DepolariseQLinkConfig
from netsquid_netbuilder.modules.qdevices import GenericQDeviceConfig
from netsquid_netbuilder.modules.qlinks.perfect import PerfectQLinkConfig

from squidasm.util.util import create_complete_graph_network # type: ignore
pwd = '/home/pgnair/stage/new_verif'

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


def init_sensing_programs(num_nodes: int, n_test: int, copies: int, failure_threshold: float):
    # Initialize node names list and select verifier node
    node_names = [f"Node_{i+1}" for i in range(num_nodes)]
    verifier = node_names[0]

    programs = {verifier: SensingProgram_verifier(verifier, node_names, n_test, copies, failure_threshold)}
    programs.update({name: SensingProgram_member(name, node_names, n_test, copies) 
                    for name in node_names if name != verifier})
    
    return programs, node_names

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
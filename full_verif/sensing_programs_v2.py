from typing import Dict, List
from pprint import pprint
import random
import numpy as np
import cmath

from squidasm.sim.stack.program import Program, ProgramContext, ProgramMeta # type: ignore
from squidasm.sim.stack.common import LogManager # type: ignore
from squidasm.sim.stack.csocket import ClassicalSocket # type: ignore
from squidasm.util.routines import create_ghz # type: ignore
from netqasm.sdk.qubit import Qubit
from netqasm.sdk.connection import BaseNetQASMConnection
from squidasm.util.util import get_qubit_state # type: ignore

###
#   Function to output a set of stabilizer generators for the GHZ state, given the number of nodes
#   The stabilizers are output in the form of a dictionary, where the key is the stabilizer name
#   and the value is a list of Pauli observables to measure for each node
#   The function selects the first stabilizer in the generator by randomly assigning 2 nodes to measure Y.
#   The remaining nodes will measure X.
#   It then increments the indices of the nodes measuring Y by 1 n-2 times to generate 
#   the n-1 such stabilizers in the generator.
#   The nth and final stabilizer is always XX...X.
#   For example:
#       if n = 5 and nodes 2 and 3 are first measuring Y
#       we will measure the stabilizer -XYYXX
#       then we will increment both indices by 1 three times 
#       to generate -XXYYX, -XXXYY, -YXXXY
#       Then finally we will measure XXXXX
###
def get_stabilizers(num_nodes: int) -> Dict[str, List[str]]:
    # Randomly assign 2 nodes to measure Y, all other nodes will measure X
    y_node1 = random.randint(0, num_nodes-1)
    y_node2 = (y_node1 + 1) % num_nodes

    stabilizer_bases = []
    stabilizer_names = []
    for s in range(1, num_nodes+1):    # Loop from 1 to n
        measure_bases = []
        name = ""
        if s == num_nodes:                      # Last stabilizer measured is necessarily XX...X
            for _ in range(num_nodes):
                measure_bases.append('X')
        else:
            name += "-"
            if y_node1 == 0:              # First two nodes measure Y
                measure_bases.extend(['Y', 'Y'])
                for _ in range(num_nodes-2):
                    measure_bases.append('X')
            elif y_node2 == 0:            # First and last nodes measure Y
                measure_bases.append('Y')
                for _ in range(num_nodes-2):
                    measure_bases.append('X')
                measure_bases.append('Y')
            else:                               # 2 nodes in the middle measure Y
                for _ in range(y_node1):
                    measure_bases.append('X')
                measure_bases.extend(['Y', 'Y'])
                for _ in range(num_nodes-1-y_node2):
                    measure_bases.append('X')

        stabilizer_bases.append(measure_bases)
        name += "".join(measure_bases)
        stabilizer_names.append(name)
        # Increment node indices that will measure Y
        y_node1 = y_node2
        y_node2 = (y_node2 + 1) % num_nodes

    result = {name: bases for name, bases in 
              zip(stabilizer_names, stabilizer_bases)}

    return result

class SensingProgram_verifier(Program):
    def __init__(self, name:str, node_names:List[str], ntest:int, send_state:bool=False):
        self.name = name
        self.node_names = node_names
        self.peer_names = [peer for peer in self.node_names if peer != self.name]
        self.num_nodes = len(self.node_names)
        self.ntest = ntest
        self.ntotal = 2 * self.num_nodes * self.ntest
        self.target_qubit = None
        self.avg_failure_rate = None
        self.phase = random.uniform(0, np.pi)
        self.send_state = send_state

    @property
    def meta(self) -> ProgramMeta:
        return ProgramMeta(
            name="GHZVerifier",
            csockets=self.peer_names,
            epr_sockets=self.peer_names,
            max_qubits=2
        )
    
    def _run_verification(self, 
                          context: ProgramContext, 
                          csockets: List[BaseNetQASMConnection]) -> None:  # type: ignore
        connection = context.connection
        logger = LogManager.get_stack_logger(f"{self.name}_Verifier")

        ### 
        # Preparation phase
        ###

        # Generate list of indices referring to copies of the GHZ state
        copies = list(range(self.ntotal))
        logger.debug(f"Available copies: {len(copies)}")

        # Generate list of stabilizers
        stabilizers = get_stabilizers(self.num_nodes)
        logger.warning(f"Stabilizers: {list(stabilizers.keys())}")
        
        # Initialize list of copy groups
        copy_groups = []

        # Randomly select ntest copies to measure each stabilizer
        for _ in range(self.num_nodes):
            selected_copies = random.sample(copies, self.ntest)
            copy_groups.append(selected_copies)
            for copy in selected_copies:
                copies.remove(copy)
        
        # Select target copy
        target = random.choice(copies)
        copy_groups.append([target])
        logger.warning(f"Copy groups: \n{copy_groups}\n")

        # Find the index of the current node
        verifier_id = self.node_names.index(self.name)
        down_epr_socket = None
        down_socket = None
        up_epr_socket = None
        up_socket = None
        # Identify down node
        if verifier_id > 0:
            down_name = self.node_names[verifier_id - 1]
            down_epr_socket = context.epr_sockets[down_name]
            down_socket = context.csockets[down_name]
        # Identify up node
        if verifier_id < len(self.node_names) - 1:
            up_name = self.node_names[verifier_id + 1]
            up_epr_socket = context.epr_sockets[up_name]
            up_socket = context.csockets[up_name]

        # Variable to hold measurement results
        results = []
        for s in range(self.num_nodes):
            results.append([[-1] * self.num_nodes for i in range(self.ntest)])

        ### 
        # GHZ distribution and measurement phase
        ###

        # We will sequentially generate ntotal GHZ state copies 
        for c in range(self.ntotal):
            ## Distribute GHZ state and get the qubit corresponding to this node ##
            qubit, _ = yield from create_ghz(
                connection,
                down_epr_socket,
                up_epr_socket,
                down_socket,
                up_socket,
                do_corrections=True
            )

            # Default action if copy index is not in one of the selected groups
            qubit_action = "discard"

            ## Identify action to be performed on qubit ##
            # Check which copy group the current copy is in
            for i in range(self.num_nodes+1):
                # Last copy group contains only the target index
                if i == self.num_nodes and c in copy_groups[i]:
                    qubit_action = "keep"
                    break
                # Otherwise, group i contains copy indices to measure w.r.t. stabilizer K_i+1
                elif c in copy_groups[i]:
                    qubit_action = "measure"
                    # Get the corresponding stabilizer
                    test_number = copy_groups[i].index(c)
                    stab_bases = list(stabilizers.values())[i]
                    stab_number = i
                    break

            logger.warning(f"Copy: {c}, qubit action: {qubit_action}")

            if qubit_action == "measure":
                logger.warning(f"Measurement: {stab_bases}")

                # Get measurement basis for the verifier node and measure the qubit
                basis = stab_bases[verifier_id]
                logger.warning(f"{self.name} will measure in {basis} basis")

                qubit.K() if basis == 'Y' else qubit.H()
                m = qubit.measure()
                yield from connection.flush()

                # Store eigenvalue result in appropriate location
                logger.debug(f"Measured result {int(m)}")
                results[stab_number][test_number][verifier_id] **= int(m)

                # Send all the other nodes the relevant info to make their measurements
                for node_index in range(1, self.num_nodes):
                    peer_index = node_index - 1
                    csocket = csockets[peer_index]
                    # Send the action to perform : 'measure'
                    csocket.send(qubit_action)
                    # Send the measurement basis
                    csocket.send(stab_bases[node_index])

                    # Receive the measurement result
                    m = yield from csocket.recv()
                    # Store eigenvalue result in appropriate location
                    logger.debug(f"Result {int(m)} received from {self.peer_names[peer_index]}")
                    results[stab_number][test_number][node_index] **= m
            
            elif qubit_action == "keep":
                # Keep qubit as target qubit
                self.target_qubit = qubit
                logger.warning(f"Copy {c} stored as target")

                yield from connection.flush()
                # Send all the other nodes the action to perform : 'keep'
                for node_index in range(1, self.num_nodes):
                    csockets[node_index - 1].send(qubit_action)

            else:   # Qubit will be deleted
                qubit.free()
                logger.warning(f"Copy {c} discarded")
                yield from connection.flush()

                # Send all the other nodes the action to perform : 'discard'
                for node_index in range(1, self.num_nodes):
                    csockets[node_index - 1].send(qubit_action)

        failure_rates = []
        # Calculate failure rate for each stabilizer measurement
        for j in range(self.num_nodes):
            measurements = np.array(results[j])
            stabilizer = list(stabilizers.keys())[j]
            logger.warning(f"Results for {stabilizer}: \n{measurements}")
            num_failures = 0
            for test in measurements:
                parity = np.prod(test)
                if str.startswith(stabilizer, "-"):
                    parity *= -1
                if parity == -1:
                    num_failures += 1
            failure_rate = num_failures / self.ntest
            failure_rates.append(failure_rate)
            logger.warning(f"Failure rate: {failure_rate}\n")

        self.avg_failure_rate = np.mean(failure_rates)
        logger.warning(f"Average failure rate: {self.avg_failure_rate}")

        """ return {"name": self.name,
                "average failure rate": self.avg_failure_rate,
                "target qubit": self.target_qubit} """
    
    def run(self, context: ProgramContext):
        connection = context.connection
        logger = LogManager.get_stack_logger(f"{self.name}_Verifier")

        # Establish classical connections to all member nodes
        csockets = [context.csockets[peer] for peer in self.peer_names]

        # Run verification protocol
        yield from self._run_verification(context, csockets)
        
        f_threshold = 1 / (2 * self.num_nodes**2)
        logger.warning(f"Threshold failure rate is {f_threshold}")

        # If failure rate below threshold
        if self.avg_failure_rate < f_threshold:
            logger.warning(f"Average failure rate below threshold. Continuing with sensing.")
            # Inform all other nodes to continue with sensing
            for csocket in csockets:
                csocket.send("continue")
            
            # Encode the phase onto target qubit
            #self.phase = 0         # to test applying no rotation
            self.target_qubit.rot_Z(angle=self.phase)

            if self.send_state is False:
                # Measure qubit in X basis
                self.target_qubit.H()
                m = self.target_qubit.measure()

                yield from connection.flush()
                logger.warning(f"{self.name} measured {int(m)}")
                
                # Return parity outcome
                return {"name": self.name,
                        "average failure rate": self.avg_failure_rate,
                        "parity": (-1)**int(m),
                        "local phase": self.phase,
                        "status": 0}
            
            else:
                logger.warning(f"Outputting unmeasured qubit")
                return {"name": self.name,
                        "average failure rate": self.avg_failure_rate,
                        "qubit": self.target_qubit,
                        "local phase": self.phase,
                        "status": 0}

        else:   # Otherwise abort the protocol
            logger.warning(f"Average failure rate not below threshold. Aborting protocol.")
            for csocket in csockets:
                csocket.send("abort")
            return {"name": self.name, 
                    "average failure rate": self.avg_failure_rate,
                    "status": 1}

    
class SensingProgram_member(Program):
    def __init__(self, name:str, node_names:List[str], ntest:int, send_state:bool=False):
        self.name = name
        self.node_names = node_names
        self.peer_names = [peer for peer in self.node_names if peer != self.name]
        self.num_nodes = len(self.node_names)
        self.ntest = ntest
        self.ntotal = 2 * self.num_nodes * self.ntest
        self.target_qubit = None
        self.phase = random.uniform(0, np.pi)
        self.send_state = send_state

    @property
    def meta(self) -> ProgramMeta:
        return ProgramMeta(
            name="GHZMember",
            csockets=self.peer_names,
            epr_sockets=self.peer_names,
            max_qubits=2
        )
    
    def _run_verification(self, context: ProgramContext, csocket: BaseNetQASMConnection):
        connection = context.connection
        logger = LogManager.get_stack_logger(f"{self.name}_Member")

        ### 
        # Preparation phase
        ###

        # Find the index of the current node
        node_id = self.node_names.index(self.name)
        down_epr_socket = None
        down_socket = None
        up_epr_socket = None
        up_socket = None
        # Identify down node
        if node_id > 0:
            down_name = self.node_names[node_id - 1]
            down_epr_socket = context.epr_sockets[down_name]
            down_socket = context.csockets[down_name]
        # Identify up node
        if node_id < len(self.node_names) - 1:
            up_name = self.node_names[node_id + 1]
            up_epr_socket = context.epr_sockets[up_name]
            up_socket = context.csockets[up_name]

        ### 
        # GHZ distribution and measurement phase 
        ###

        # We will sequentially generate ntotal GHZ state copies 
        for c in range(self.ntotal):
            ## Distribute GHZ state and get the qubit corresponding to this node ##
            qubit, _ = yield from create_ghz(
                connection,
                down_epr_socket,
                up_epr_socket,
                down_socket,
                up_socket,
                do_corrections=True
            )
            
            ## Get action to be performed by the Verifier ##
            qubit_action = yield from csocket.recv()

            logger.warning(f"Copy: {c}, Received qubit action: {qubit_action}")

            if qubit_action == "measure":
                # Measure the qubit in the given basis
                basis = yield from csocket.recv()
                logger.warning(f"{self.name} will measure in {basis} basis")

                qubit.K() if basis == 'Y' else qubit.H()
                m = qubit.measure()
                yield from connection.flush()

                # Send the result back to Verifier
                csocket.send(int(m))
                logger.debug(f"Result {int(m)} sent to Verifier")
            
            elif qubit_action == "keep":
                self.target_qubit = qubit
                logger.warning(f"Copy {c} stored as target")
                yield from connection.flush()

            else:   # Qubit will be deleted
                qubit.free()
                logger.warning(f"Copy {c} discarded")
                yield from connection.flush()

        return {"name": self.name, "target qubit": self.target_qubit}
    
    def run(self, context: ProgramContext):
        connection = context.connection
        logger = LogManager.get_stack_logger(f"{self.name}_Member")

        # Establish classical connection with Verifier node
        csocket = context.csockets[self.node_names[0]]

        # Run verification protocol
        yield from self._run_verification(context, csocket)

        action = yield from csocket.recv()
        logger.warning(f"Received message: {action} from Verifier")

        if action == "continue":
            # Encode the phase onto target qubit
            #self.phase = 0         # to test applying no rotation
            self.target_qubit.rot_Z(angle=self.phase)          

            if self.send_state is False:
                # Measure qubit in X basis
                self.target_qubit.H()
                m = self.target_qubit.measure()

                yield from connection.flush()
                logger.warning(f"{self.name} measured {int(m)}")

                return {"name": self.name, 
                        "parity": (-1)**int(m),
                        "local phase": self.phase}
            
            else:
                # Last node will output the density matrix of the shared state
                if self.name == self.node_names[-1]:
                    full_state = get_qubit_state(self.target_qubit, self.name, full_state=True)
                    logger.warning(f"Outputting density matrix of shared state")
                    return {"name": self.name,
                            "qubit": self.target_qubit, 
                            "full state": full_state,
                            "local phase": self.phase}

                else:
                    logger.warning(f"Outputting unmeasured qubit")
                    return {"name": self.name, 
                            "qubit": self.target_qubit,
                            "local phase": self.phase}
        
        else:
            logger.warning(f"Sensing protocol aborted")
            return {"name": self.name}


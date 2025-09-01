from typing import Dict, List
from pprint import pprint
import random
import numpy as np
import gc

from squidasm.sim.stack.program import Program, ProgramContext, ProgramMeta # type: ignore
from squidasm.sim.stack.common import LogManager # type: ignore
from squidasm.util.util import get_qubit_state # type: ignore
from netqasm.sdk.qubit import Qubit

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

####
#   Class that describes the GHZ verification protocol being performed 
#   when the nodes share a separable |+...+> state
#   from the Verifier's perspective
####
class GHZVerifier_plus_states(Program):
    def __init__(self, name:str, node_names:List[str], ntest:int):
        self.name = name
        self.node_names = node_names
        self.peer_names = [peer for peer in self.node_names if peer != self.name]
        self.num_nodes = len(self.node_names)
        self.ntest = ntest
        self.ntotal = 2 * self.num_nodes * self.ntest

    @property
    def meta(self) -> ProgramMeta:
        return ProgramMeta(
            name="GHZVerifier",
            csockets=self.peer_names,
            epr_sockets=self.peer_names,
            max_qubits=2
        )
    
    def run(self, context: ProgramContext):
        connection = context.connection
        logger = LogManager.get_stack_logger(f"{self.name}_Verifier")

        ###
        #   Preparation phase
        ###

        # Generate list of indices referring to copies of the state
        copies = list(range(self.ntotal))
        logger.warning(f"Available copies: {len(copies)}")

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

        # Variable to hold target qubit
        target_qubit = None

        # Variable to hold measurement results
        results = []
        for s in range(self.num_nodes):
            results.append([[-1] * self.num_nodes for i in range(self.ntest)])

        # Establish classical connections to all member nodes
        csockets = [context.csockets[peer] for peer in self.peer_names]

        # Find the index of the current node
        verifier_id = self.node_names.index(self.name)

        ###
        #   State distribution and measurement phase
        ###

        # We will sequentially generate ntotal state copies 
        for c in range(self.ntotal):
            ## Get local plus state ##
            qubit = Qubit(connection)
            qubit.H()

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
                    logger.debug(f"{self.peer_names[peer_index]} will measure in {stab_bases[node_index]} basis")
                    # Receive the measurement result
                    m = yield from csocket.recv()

                    # Store eigenvalue result in appropriate location
                    logger.debug(f"Result {int(m)} received from {self.peer_names[peer_index]}")
                    results[stab_number][test_number][node_index] **= m

            elif qubit_action == "keep":
                # Keep qubit as target qubit
                target_qubit = qubit
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

        avg_failure_rate = np.mean(failure_rates)
        logger.warning(f"Average failure rate: {avg_failure_rate}")

        density_mat = get_qubit_state(target_qubit, self.name)

        return {"name": self.name,
                "failure rates": failure_rates,
                "average failure rate": avg_failure_rate,
                "target qubit": target_qubit,
                "target state": density_mat}

####
#   Class that describes the GHZ verification protocol being performed 
#   when the nodes share a separable |+...+> state
#   from the member nodes' perspective
####
class GHZMember_plus_states(Program):
    def __init__(self, name:str, node_names:List[str], ntest:int):
        self.name = name
        self.node_names = node_names
        self.peer_names = [peer for peer in self.node_names if peer != self.name]
        self.num_nodes = len(self.node_names)
        self.ntest = ntest
        self.ntotal = 2 * self.num_nodes * self.ntest

    @property
    def meta(self) -> ProgramMeta:
        return ProgramMeta(
            name="GHZMember",
            csockets=self.peer_names,
            epr_sockets=self.peer_names,
            max_qubits=2
        )
    
    def run(self, context: ProgramContext):
        connection = context.connection
        logger = LogManager.get_stack_logger(f"{self.name}_Member")

        ### 
        # Preparation steps
        ###

        # Variable to hold target qubit
        target_qubit = None

        # Establish classical connection with Verifier node
        csocket = context.csockets[self.node_names[0]]

        ### 
        # Verification protocol 
        ###

        # We will sequentially generate ntotal state copies
        for c in range(self.ntotal):
            ## Get local plus state ##
            qubit = Qubit(connection)
            qubit.H()

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
                target_qubit = qubit
                logger.warning(f"Copy {c} stored as target")
                yield from connection.flush()

            else:   # Qubit will be deleted
                qubit.free()
                logger.warning(f"Copy {c} discarded")
                yield from connection.flush()

        density_mat = get_qubit_state(target_qubit, self.name)
        return {"name": self.name, 
                "target qubit": target_qubit,
                "target state": density_mat}
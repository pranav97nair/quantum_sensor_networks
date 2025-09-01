from typing import Dict, List
from pprint import pprint
import random
import numpy as np
import gc

from squidasm.sim.stack.program import Program, ProgramContext, ProgramMeta # type: ignore
from squidasm.util.routines import create_ghz # type: ignore

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

###
#   This class defines the program run by the Verifier node of the quantum network.
#   As of now, the first node in node_names is automatically selected as the Verifier.
#
#   In the run method, we divide the protocol into two phases:
#
#       Preparation phase:
#       1.  The Verifier uses 'get_stabilizers()' to initialize the list of stabilizer generators to measure.
#       2.  It initializes a list of indices {0,1,...,ntotal-1} refering to the copies
#           of the GHZ state to be distributed.
#       3.  For each stabilizer K_s, it randomly selects ntest copies from the above list 
#           to be measured and adds them as an entry in an array called copy_groups.
#       4.  It randomly selects one copy as the target and adds it as the final entry in copy_groups. 
#           The remaining copies will be discarded.
#       5.  It identifies its neighboring nodes for the GHZ state creation.
#       6.  It initializes a variable to hold the target qubit.
#       7.  It initializes a 3D-array results to hold the measurement results of the size n x ntest x n.
#           The first dimension corresponds to the stabilizers, 
#           the second to the copies measured for each stabilizer, 
#           and the third to the results from the individual nodes for each copy measured.
#       8.  Before starting the state distrubution, the Verifier establishes classical communication 
#           channels with each of the other nodes in the network.
#
#       GHZ distribution and measurement phase:
#
#       The following steps 1-3 are performed ntotal times
#       1.  Generate a GHZ state with the other nodes in the network using 'create_ghz()'.
#       2.  The Verifier checks whether the index of the current GHZ copy is in one of the preselected 
#           copy groups to determine what action needs to be performed with the copy.
#       3a. Qubit action = discard
#           If the copy is not in one of the groups, the Verifier frees its qubit from memory and sends 
#           the message 'discard' to all the other nodes, so they will do the same.
#       3b. Qubit action = measure
#           If the copy is in group i < n, the copy will be measured w.r.t. to stabilizer K_i+1.
#           1.  The Verifier measures its qubit in its corresponding basis and stores the result by
#               updating the appropriate entry in the results array.
#           2.  It sends the message 'measure' and the corresponding measurement bases to all 
#               the other nodes in the network.
#           3.  It receives the measurement results from all the other nodes and stores the results.
#       3c. Qubit action = keep
#           If the copy is in the final group, it is the target copy.
#           The Verifier stores its qubit and sends the message 'keep' to all other nodes.
#
#       4.  The Verifier calculates the failure rate for each stabilizer, as follows:
#           1. It calculates the overall parity of the results for each of the ntest copies.
#           2. If the overall parity is -1, it records it as a failure.
#           3. For each stabilizer, the failure rate is the number of failures divided by ntest
#
#       5.  The Verifier outputs a list of the failure rates for all stabilizers, 
#           the average of the failure rates, and its target qubit.
###
class GHZVerifierNode_v2(Program):
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

        ### 
        # Preparation phase
        ###

        # Generate list of indices referring to copies of the GHZ state
        copies = list(range(self.ntotal))
        #print(f"Available copies: {len(copies)}")

        # Generate list of stabilizers
        stabilizers = get_stabilizers(self.num_nodes)
        #print(f"Stabilizers: {list(stabilizers.keys())}")
        
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
        
        #print(f"Copy groups: \n{copy_groups}\n")

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

        # Variable to hold target qubit
        target_qubit = None

        # Variable to hold measurement results
        results = []
        for s in range(self.num_nodes):
            results.append([[-1] * self.num_nodes for i in range(self.ntest)])

        # Establish classical connections to all member nodes
        csockets = [context.csockets[peer] for peer in self.peer_names]

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
            #print(f"Now working with: Copy {c}")

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
            
            #print(f"Qubit action: {qubit_action}")

            if qubit_action == "measure":
                #print(f"Measurement: {stab_bases}")

                # Get measurement basis for the verifier node and measure the qubit
                basis = stab_bases[verifier_id]
                #print(f"{self.name} will measure in {basis} basis")
                qubit.K() if basis == 'Y' else qubit.H()
                m = qubit.measure()
                yield from connection.flush()
                # Store eigenvalue result in appropriate location
                #print(f"{self.name} measured {int(m)}")
                results[stab_number][test_number][verifier_id] **= int(m)

                # Send all the other nodes the relevant info to make their measurements
                for node_index in range(1, self.num_nodes):
                    peer_index = node_index - 1
                    csocket = csockets[peer_index]
                    # Send the action to perform : 'measure'
                    csocket.send(qubit_action)
                    # Send the measurement basis
                    csocket.send(stab_bases[node_index])
                    #print(f"{self.peer_names[peer_index]} will measure in {stab_bases[node_index]} basis")
                    # Receive the measurement result
                    m = yield from csocket.recv()
                    # Store eigenvalue result in appropriate location
                    #print(f"{self.peer_names[peer_index]} measured {int(m)}")
                    results[stab_number][test_number][node_index] **= m
            
            elif qubit_action == "keep":
                # Keep qubit as target qubit
                target_qubit = qubit
                #print(f"Copy {c} is the target")
                yield from connection.flush()
                # Send all the other nodes the action to perform : 'keep'
                for node_index in range(1, self.num_nodes):
                    csockets[node_index - 1].send(qubit_action)

            else:   # Qubit will be deleted
                #print(f"Copy {c} will be discarded")
                qubit.free()
                yield from connection.flush()
                # Send all the other nodes the action to perform : 'discard'
                for node_index in range(1, self.num_nodes):
                    csockets[node_index - 1].send(qubit_action)
            #print("")

        failure_rates = []
        # Calculate failure rate for each stabilizer measurement
        for j in range(self.num_nodes):
            measurements = np.array(results[j])
            stabilizer = list(stabilizers.keys())[j]
            #print(f"Results for {stabilizer}: \n{measurements}")
            num_failures = 0
            for test in measurements:
                parity = np.prod(test)
                if str.startswith(stabilizer, "-"):
                    parity *= -1
                if parity == -1:
                    num_failures += 1
            failure_rate = num_failures / self.ntest
            failure_rates.append(failure_rate)
            #print(f"Failure rate: {failure_rate}\n")

        avg_failure_rate = np.mean(failure_rates)
        #print(f"Average failure rate: {avg_failure_rate}")

        return {"name": self.name, 
                "failure rates": failure_rates,
                "average failure rate": avg_failure_rate,
                "target qubit": target_qubit}
    

###
#   This class defines the program run by the member nodes of the quantum network.
#   As of now, the first node in node_names is automatically selected as the Verifier.
#
#   In the run method, we divide the protocol into two phases:
#
#       Preparation phase:
#       1.  The node identifies its neighboring nodes for the GHZ state creation.
#       2.  It initializes a variable to hold the target qubit.
#       3.  Before starting the state distrubution, the node establishes a classical communication 
#           channel with the Verifier.
#
#       GHZ distribution and measurement phase:
#
#       The following steps 1-3 are performed ntotal times
#       1.  Generate a GHZ state with the other nodes in the network using 'create_ghz()'.
#       2.  The node receives the message from the Verifier indicating the action to perform on the qubit.
#       3a. If qubit action = discard, the node frees the qubit from its quantum memory.
#       3b. If qubit action = measure,
#           1.  The node receives the message from the Verifier indicating its measurement basis.
#           2.  It measures its qubit accordingly and sends the result to the Verifier.
#       3c. If qubit action = keep, the node stores its qubit as the target qubit.
#
#       4.  The node outputs its target qubit.
###
class GHZMemberNode_v2(Program):
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

        ### 
        # Preparation steps
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

        # Variable to hold target qubit
        target_qubit = None

        # Establish classical connection with Verifier node
        csocket = context.csockets[self.node_names[0]]

        ### 
        # Verification protocol 
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

            if qubit_action == "measure":
                # Measure the qubit in the given basis
                basis = yield from csocket.recv()
                qubit.K() if basis == 'Y' else qubit.H()
                m = qubit.measure()
                yield from connection.flush()

                # Send the result back to Verifier
                csocket.send(int(m))
            
            elif qubit_action == "keep":
                target_qubit = qubit
                yield from connection.flush()

            else:   # Qubit will be deleted
                qubit.free()
                yield from connection.flush()
            
        return {"name": self.name, "target qubit": target_qubit}
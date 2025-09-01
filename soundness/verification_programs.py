from typing import List
from pprint import pprint
import random
import numpy as np
import gc

from squidasm.sim.stack.program import Program, ProgramContext, ProgramMeta # type: ignore
from squidasm.util.routines import create_ghz # type: ignore

from squidasm.util.util import get_qubit_state # type: ignore

###
#   This class defines the program run by the Verifier node of the quantum network.
#   As of now, the first node in node_names is automatically selected as the Verifier.
#
#   In the run method:
#       First, we define the protocol for distributing ntotal copies of a GHZ state.
#       This protocol outputs the qubits held by the node running the program.
#
#       Then, we define the verification protocol from the Verifier's side:
#       1.  The Verifier establishes classical communication channels with each of the other nodes in the network.
#       2.  It identifies the first stabilizer to measure by selecting which two nodes will measure Y. The rest will measure X. 
#           Then, looping over s from 1 to n:
#           a. It randomly selects ntest copies to be measured w.r.t. the stabilizer K_s.
#           b. To each of the other nodes, the Verifier sends their measurement basis and the indices of the ntest copies.
#           c. It identifies its own measurement basis and then measures the selected copies.
#           d. The Verifier receives the measurement results from all the other nodes and combines them with its own results.
#           e. It calculates the overall parity of the results for each of the ntest copies.
#           f. If the overall parity is -1, it records it as a failure and calculates the failure rate. 
#           g. The nth and final stabilizer measured is always XX...X
#       3.  The Verifier randomly selects the index of the target copy for the sensing protocol and communicates it to the other nodes.
#       4.  It extracts its target qubit and discards the remaining ones.
#       5.  It outputs the average failure rate over all stabilizers and its target qubit.
###
class GHZProgram_verifier(Program):
    def __init__(self, name: str, node_names: List[str], ntest: int):
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
            max_qubits=self.ntotal,
        )
    
    def run(self, context: ProgramContext):
        connection = context.connection

        ### 
        # Protocol to distribute GHZ states with peer nodes 
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
        
        copies = list(range(self.ntotal))
        #print(f"Total number of copies: {len(copies)}")

        qubits = []
        # Get the appropriate qubit from each of the ntotal GHZ copies
        for c in copies:
            qubit, _ = yield from create_ghz(
                connection,
                down_epr_socket,
                up_epr_socket,
                down_socket,
                up_socket,
                do_corrections=True
            )
            #print(f"{self.name} has qubit {c+1}")
            qubits.append(qubit)
            yield from connection.flush()
        
        # Test return statement to check if GHZ distribution worked
        #return {"name": self.name, "qubits": qubits}


        ### 
        # Verification protocol
        ###

        # Establish classical connections to all member nodes
        csockets = [context.csockets[peer] for peer in self.peer_names]

        # Initialize list for looping over n stabilizers
        stabilizers = list(range(1, self.num_nodes+1))

        # Initialize list to store failure rates for each stabilizer measurement
        failure_rates = []

        # Randomly assign 2 nodes to measure Y, all other nodes will measure X
        # For example:
        #   if n = 5 and nodes 2 and 3 are measuring Y
        #   we will measure the stabilizer -XYYXX
        #   we will then increment both indices by 1 n-1 times
        #   Then finally we will measure XXXXX
        y_node1 = random.randint(0, self.num_nodes-1)
        y_node2 = (y_node1 + 1) % self.num_nodes

        #print(f"Number of copies to be tested for each stabilizer: {self.ntest}\n")
        for s in stabilizers:    
            # We want to make the stabilizer measurement given by the node indices measuring Y
            # Determine measurement bases for all nodes and the corresponding stabilizer      
            measure_bases = []
            stabilizer_name = ""
            if s == self.num_nodes:                 # Last stabilizer measured is necessarily XX...X
                for _ in range(self.num_nodes):
                    measure_bases.append('X')
            else:
                stabilizer_name += "-"
                if node_id == y_node1:              # First two nodes measure Y
                    measure_bases.extend(['Y', 'Y'])
                    for _ in range(self.num_nodes-2):
                        measure_bases.append('X')
                elif node_id == y_node2:            # First and last nodes measure Y
                    measure_bases.append('Y')
                    for _ in range(self.num_nodes-2):
                        measure_bases.append('X')
                    measure_bases.append('Y')
                else:                               # 2 nodes in the middle measure Y
                    for _ in range(y_node1):
                        measure_bases.append('X')
                    measure_bases.extend(['Y', 'Y'])
                    for _ in range(self.num_nodes-1-y_node2):
                        measure_bases.append('X')

            stabilizer_name += "".join(measure_bases)
            #print(f"Stabilizer: K{s} = {stabilizer_name}")
                    
            # Randomly select ntest copies to measure
            measure_Ks = random.sample(copies, self.ntest)
            #print(f"Copies selected for measurement: {measure_Ks}")

            # Identify measurement basis for Verifier node
            basis = measure_bases[node_id]
            #print(f"{self.name} will measure in {basis} basis")

            # Send all the other nodes the relevant info to make their measurements
            for node_index in range(1, self.num_nodes):
                peer_index = node_index - 1
                csocket = csockets[peer_index]
                # Notify which copies to measure
                csocket.send(measure_Ks)
                # Notify which observable to measure
                csocket.send(measure_bases[node_index])
                #print(f"{self.peer_names[peer_index]} will measure in {measure_bases[node_index]} basis")
                
            # Make measurement
            local_results = []
            for c in measure_Ks:
                qubits[c].K() if basis == 'Y' else qubits[c].H()
                m = qubits[c].measure()
                local_results.append(m)
                yield from connection.flush()
                # Discard measured qubit
                copies.remove(c)
                qubits[c] = None

            # Combine measurement results with those received from peer nodes
            measurements = np.array([(-1)**int(r) for r in local_results])
            for csocket in csockets:
                peer_x_results = yield from csocket.recv()
                measurements = np.vstack((measurements, peer_x_results))

            # Calculate failure rate
            measurements = measurements.transpose()
            num_failures = 0
            #print("Measurement results:")
            for i in range(self.ntest):
                result = measurements[i]
                parity = np.prod(result)
                if s < self.num_nodes: parity *= -1
                #print(f"Test {i+1}: {result}, Parity: {parity}")
                if parity != 1: num_failures += 1
            failure_rate = num_failures / self.ntest
            #print(f"Failure rate: {failure_rate} \n")
            failure_rates.append(failure_rate)
            del measurements
            
            # Increment node indices that will measure Y
            y_node1 = y_node2
            y_node2 = (y_node2 + 1) % self.num_nodes

        # Randomly select target copy for sensing protocol and communicate it to other nodes
        target_id = random.choice(copies)
        #print(f"Copies remaining: {copies} \n")
        #print(f"Verifier selected copy {target_id} as target\n")
        for csocket in csockets:
            csocket.send(target_id)
        
        # Get qubit from target copy and discard all others
        target = qubits[target_id]
        del qubits
        collected = gc.collect()
        
        avg_failure_rate = np.average(failure_rates)
        return {"name": self.name, "average failure rate": avg_failure_rate, "target qubit": target}

###
#   This class defines the program run by all nodes of the network except the Verifier.
#   As of now, the first node in node_names is selected as the Verifier.
#   Therefore this program is run by nodes 2 to n.
#
#   In the run method:
#       First, we define the protocol for distributing ntotal copies of a GHZ state.
#       This protocol outputs the qubits held by the node running the program.
#
#       Then, we define the verification protocol from the member nodes' side:
#       1.  Each node establishes a classical communication channel with the Verifier.
#       2.  Looping over s from 1 to n:
#           a. Each node receives from the Verifier:
#               -the indices of the ntest copies to be measured w.r.t. the stabilizer K_s 
#               -and their measurement basis.
#           b. Each node then measures the selected copies accordingly.
#           c. Each node sends the measurement results (+1, -1) to the Verifier.
#       3.  Each node receives the index of the target copy for the sensing protocol selected by the Verifier.
#       4.  Each node extracts its target qubit and discards the remaining ones.
#       5.  It outputs the target qubit.
###
class GHZProgram_member(Program):
    def __init__(self, name: str, node_names: List[str], ntest: int):
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
            max_qubits=self.ntotal,
        )
    
    def run(self, context: ProgramContext):
        connection = context.connection
        ### 
        # Protocol to distribute GHZ states with peer nodes 
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
        
        copies = list(range(self.ntotal))
        qubits = []
        # Get the appropriate qubit from each of the ntotal GHZ states
        for c in copies:
            qubit, _ = yield from create_ghz(
                connection,
                down_epr_socket,
                up_epr_socket,
                down_socket,
                up_socket,
                do_corrections=True
            )
            #print(f"{self.name} has qubit {c+1}")
            qubits.append(qubit)
            yield from connection.flush()

        # Test return statement to check if GHZ distribution worked
        #return {"name": self.name, "qubits": qubits}

        ### 
        # Verification protocol
        ###

        # Establish classical connection with Verifier node
        csocket = context.csockets[self.node_names[0]]

        # Initialize list to loop over n stabilizers
        stabilizers = list(range(1, self.num_nodes+1))

        for s in stabilizers:
            # Receive indices for the copies to be measured
            measure_Ks = yield from csocket.recv()
            # Receive measurement basis from Verifier
            basis = yield from csocket.recv()
            #print(f"{self.name} will measure in {basis} basis")

            # Make measurement
            local_results = []
            for c in measure_Ks:
                qubits[c].K() if basis == 'Y' else qubits[c].H()
                m = qubits[c].measure()
                local_results.append(m)
                yield from connection.flush()

                # Discard measured qubit
                copies.remove(c)   
                qubits[c] = None
            
            # Send results to Verifier
            local_results = [(-1)**int(r) for r in local_results]
            csocket.send(local_results)

        # Receive target copy id selected by Verifier ndoe
        target_id = yield from csocket.recv()

        # Get qubit from target copy and discard all others
        target = qubits[target_id]
        del qubits
        collected = gc.collect()

        return {"name": self.name, "target qubit": target}
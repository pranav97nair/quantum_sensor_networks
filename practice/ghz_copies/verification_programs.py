from typing import List
from pprint import pprint
import random
import numpy as np

from netqasm.sdk.qubit import QubitMeasureBasis
from squidasm.sim.stack.program import Program, ProgramContext, ProgramMeta # type: ignore
from squidasm.util.routines import create_ghz # type: ignore

from squidasm.util.util import get_qubit_state # type: ignore


class GHZProgram_verifierX(Program):
    def __init__(self, name: str, node_names: List[str], ntest: int):
        self.name = name
        self.node_names = node_names
        self.peer_names = [peer for peer in self.node_names if peer != self.name]
        self.num_nodes = len(self.node_names)
        self.ntest = ntest
        self.ntotal = 2 * self.ntest * self.num_nodes

    @property
    def meta(self) -> ProgramMeta:
        return ProgramMeta(
            name="GHZVerifier",
            csockets=self.peer_names,
            epr_sockets=self.peer_names,
            max_qubits=2,
        )
    
    def run(self, context: ProgramContext):
        connection = context.connection
        ### Implement protocol to distribute GHZ states with peer nodes ###

        # Find the index of the current node
        i = self.node_names.index(self.name)
        down_epr_socket = None
        down_socket = None
        up_epr_socket = None
        up_socket = None
        # Identify down node
        if i > 0:
            down_name = self.node_names[i - 1]
            down_epr_socket = context.epr_sockets[down_name]
            down_socket = context.csockets[down_name]
        # Identify up node
        if i < len(self.node_names) - 1:
            up_name = self.node_names[i + 1]
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
            qubits.append(qubit)
            yield from connection.flush()

        # Establish classical connections to all member nodes
        csockets = [context.csockets[peer] for peer in self.peer_names]

        # Randomly select n_test qubits to measure X and send them to peers
        measure_X = random.sample(copies, self.ntest)
        for csocket in csockets:
            csocket.send(measure_X)

        # Make measurement
        local_x_results = []
        for c in measure_X:
            qubits[c].H()
            m = qubits[c].measure()
            local_x_results.append(m)
            yield from connection.flush()
            # Discard measured qubit
            copies.remove(c)
            qubits[c] = None

        # Combine measurement results with those received from peer nodes
        measurements = np.array([(-1)**int(r) for r in local_x_results])
        for csocket in csockets:
            peer_x_results = yield from csocket.recv()
            measurements = np.vstack((measurements, peer_x_results))

        # Calculate failure rate
        measurements = measurements.transpose()
        print(measurements)
        num_failures = 0
        for result in measurements:
            parity = np.prod(result)
            if parity != 1: num_failures += 1
        failure_rate = num_failures / self.ntest
                

        return {"name": self.name, "qubits": qubits, "failure rate": failure_rate}
            
class GHZProgram_memberX(Program):
    def __init__(self, name: str, node_names: List[str], ntest: int):
        self.name = name
        self.node_names = node_names
        self.peer_names = [peer for peer in self.node_names if peer != self.name]
        self.num_nodes = len(self.node_names)
        self.ntest = ntest
        self.ntotal = 2 * self.ntest * self.num_nodes

    @property
    def meta(self) -> ProgramMeta:
        return ProgramMeta(
            name="GHZMember",
            csockets=self.peer_names,
            epr_sockets=self.peer_names,
            max_qubits=2,
        )
    
    def run(self, context: ProgramContext):
        connection = context.connection
        ### Implement protocol to distribute GHZ states with peer nodes ###

        # Find the index of the current node
        i = self.node_names.index(self.name)
        down_epr_socket = None
        down_socket = None
        up_epr_socket = None
        up_socket = None
        # Identify down node
        if i > 0:
            down_name = self.node_names[i - 1]
            down_epr_socket = context.epr_sockets[down_name]
            down_socket = context.csockets[down_name]
        # Identify up node
        if i < len(self.node_names) - 1:
            up_name = self.node_names[i + 1]
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
            qubits.append(qubit)
            yield from connection.flush()

        # Establish classical connection with Verifier node
        csocket = context.csockets[self.node_names[0]]
        measure_X = yield from csocket.recv()

        # Make measurement
        local_x_results = []
        for c in measure_X:
            qubits[c].H()
            m = qubits[c].measure()
            local_x_results.append(m)
            yield from connection.flush()
            # Discard measured qubit
            copies.remove(c)   
            qubits[c] = None
        
        # Send results to verifier
        local_x_results = [(-1)**int(r) for r in local_x_results]
        csocket.send(local_x_results)

        return {"name": self.name, "qubits": qubits}
        
class GHZProgram_verifier(Program):
    def __init__(self, name: str, node_names: List[str], ntest: int):
        self.name = name
        self.node_names = node_names
        self.peer_names = [peer for peer in self.node_names if peer != self.name]
        self.num_nodes = len(self.node_names)
        self.ntest = ntest
        self.ntotal = 2 * self.ntest * self.num_nodes

    @property
    def meta(self) -> ProgramMeta:
        return ProgramMeta(
            name="GHZVerifier",
            csockets=self.peer_names,
            epr_sockets=self.peer_names,
            max_qubits=2,
        )
    
    def run(self, context: ProgramContext):
        connection = context.connection

        ### 
        # Implement protocol to distribute GHZ states with peer nodes 
        ###

        # Find the index of the current node
        i = self.node_names.index(self.name)
        down_epr_socket = None
        down_socket = None
        up_epr_socket = None
        up_socket = None
        # Identify down node
        if i > 0:
            down_name = self.node_names[i - 1]
            down_epr_socket = context.epr_sockets[down_name]
            down_socket = context.csockets[down_name]
        # Identify up node
        if i < len(self.node_names) - 1:
            up_name = self.node_names[i + 1]
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
            qubits.append(qubit)
            yield from connection.flush()

        # Establish classical connections to all member nodes
        csockets = [context.csockets[peer] for peer in self.peer_names]

        # Initialize list of stabilizers #
        stabilizers = list(range(1, self.num_nodes+1))
        
        ### 
        # Implement protocol to measure all stabilizers 
        ###

        # Array to store failure rate calculated for each stabilizer measurement
        failure_rates =[]

        # Randomly assign 2 nodes to measure Y, all other nodes will measure X
        # For example:
        #   if n = 5 and nodes 2 and 3 are measuring Y
        #   we will measure the stabilizer -XYYXX
        #   we will then increment the 2 indices by 1 n-1 times
        #   On the nth (last) round, we will measure XXXXX
        y_node1 = random.randint(0, self.num_nodes-1)
        y_node2 = (y_node1 + 1) % self.num_nodes

        round = 1
        print(f"Copies available: {copies}")
        for s in stabilizers:
            print(f"Stabilizer: K_{round}")
            if round < self.num_nodes:
                print(f"y_nodes: {y_node1}, {y_node2}")
            # We want to measure stabilizer K_s
            # Randomly select ntest copies to measure
            measure_Ks = random.sample(copies, self.ntest)
            print(f"Copies selected for measurement: {measure_Ks}")

            # Send the relevant measurement info to all other nodes
            for peer_index in range(self.num_nodes-1):
                csocket = csockets[peer_index]
                # Notify which copies to measure
                csocket.send(measure_Ks)
    
                node_index = peer_index + 1
                # Notify which observable to measure
                if round == self.num_nodes:
                    csocket.send('X')
                elif node_index == y_node1 or node_index == y_node2:
                    csocket.send('Y')
                else:
                    csocket.send('X')
                
            # Identify measurement basis for Verifier node
            if round == self.num_nodes:
                basis = 'X'
            elif i == y_node1 or i == y_node2:
                basis = 'Y'
            else:
                basis = 'X'

            print(f"{self.name} will measure in {basis} basis")
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
            print(f"Measurement results: \n{measurements}")
            num_failures = 0
            for result in measurements:
                parity = np.prod(result)
                if round < self.num_nodes: parity *= -1
                if parity != 1: num_failures += 1
            print(f"Failures: {num_failures}")
            failure_rates.append(num_failures / self.ntest)
            
            y_node1 = y_node2
            y_node2 = (y_node2 + 1) % self.num_nodes
            round += 1
            print(f"Copies remaining: {copies}")

        avg_failure_rate = np.average(failure_rates)
        return {"name": self.name, "average failure rate": avg_failure_rate}
            
class GHZProgram_member(Program):
    def __init__(self, name: str, node_names: List[str], ntest: int):
        self.name = name
        self.node_names = node_names
        self.peer_names = [peer for peer in self.node_names if peer != self.name]
        self.num_nodes = len(self.node_names)
        self.ntest = ntest
        self.ntotal = 2 * self.ntest * self.num_nodes

    @property
    def meta(self) -> ProgramMeta:
        return ProgramMeta(
            name="GHZMember",
            csockets=self.peer_names,
            epr_sockets=self.peer_names,
            max_qubits=2,
        )
    
    def run(self, context: ProgramContext):
        connection = context.connection
        ### 
        # Implement protocol to distribute GHZ states with peer nodes 
        ###

        # Find the index of the current node
        i = self.node_names.index(self.name)
        down_epr_socket = None
        down_socket = None
        up_epr_socket = None
        up_socket = None
        # Identify down node
        if i > 0:
            down_name = self.node_names[i - 1]
            down_epr_socket = context.epr_sockets[down_name]
            down_socket = context.csockets[down_name]
        # Identify up node
        if i < len(self.node_names) - 1:
            up_name = self.node_names[i + 1]
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
            qubits.append(qubit)
            yield from connection.flush()

        # Establish classical connection with Verifier node
        csocket = context.csockets[self.node_names[0]]

        # Initialize list of stabilizers
        stabilizers = list(range(1, self.num_nodes+1))

        ### 
        # Implement protocol to measure all stabilizers 
        ###

        for s in stabilizers:
            # Receive indices for the copies to be measured
            measure_Ks = yield from csocket.recv()
            # Receive measurement basis from Verifier
            basis = yield from csocket.recv()
            print(f"{self.name} will measure in {basis} basis")

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

        return {"name": self.name, "qubits": qubits}
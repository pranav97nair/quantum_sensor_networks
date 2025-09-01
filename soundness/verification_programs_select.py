from typing import Dict, List
from itertools import combinations
from pprint import pprint
import random
import numpy as np
import gc

from squidasm.sim.stack.program import Program, ProgramContext, ProgramMeta # type: ignore
from squidasm.sim.stack.common import LogManager # type: ignore
from squidasm.util.routines import create_ghz # type: ignore
from netqasm.sdk.qubit import Qubit
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
def get_generators(num_nodes: int) -> Dict[str, List[str]]:
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
#       1.  The Verifier uses 'get_generators()' to initialize the list of stabilizer generators to measure
#       2.  It initializes a list of indices {0,1,...,ntotal-1} refering to the copies 
#           of the GHZ state to be distributed
#       3.  For each stabilizer K_s, it randomly selects ntest copies from the above list 
#           to be measured and adds them as an entry in an array called copy_groups
#       4.  It randomly selects one copy as the target and adds it as the final entry in copy_groups. 
#           The remaining copies will be discarded
#       5.  It identifies its neighboring nodes for the GHZ state creation.
#       6.  It initializes variables to hold the target qubit and the qubits to be discarded
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
#       1.  Generate a GHZ state with the other nodes in the network using 'create_ghz()'
#       2.  The Verifier checks whether the index of the current GHZ copy is in one of the preselected 
#           copy groups to determine what action needs to be performed with the copy.
#       3a. Qubit action = discard
#           If the copy is not in one of the groups, the Verifier marks its qubit for deletion and sends 
#           the message 'discard' to all the other nodes, so they will do the same.
#       3b. Qubit action = measure
#           If the copy is in group i < n, the copy will be measured w.r.t. to stabilizer K_i+1
#           1.  The Verifier measures its qubit in its corresponding basis and stores the result by
#               updating the appropriate entry in the results array.
#           2.  It sends the message 'measure' and the corresponding measurement bases to all 
#               the other nodes in the network
#           3.  It receives the measurement results from all the other nodes and stores the results.
#       3c. Qubit action = keep
#           If the copy is in the final group, it is the target copy.
#           The Verifier stores its qubit and sends the message 'keep' to all other nodes
#
#       4.  The Verifier discards its unused qubits from memory.
#       5.  The Verifier calculates the failure rate for each stabilizer.
#           a. It calculates the overall parity of the results for each of the ntest copies.
#           b. If the overall parity is -1, it records it as a failure.
#           c. For each stabilizer, the failure rate is the number of failures divided by ntest
#       6.  The Verifier outputs a list of the failure rates for all stabilizers, 
#           the average of the failure rates, and its target qubit.
###
class GHZVerifierNode_select(Program):
    def __init__(self, name:str, node_names:List[str], ntest:int, stab_tests:int):
        self.name = name
        self.node_names = node_names
        self.peer_names = [peer for peer in self.node_names if peer != self.name]
        self.num_nodes = len(self.node_names)
        self.ntest = ntest
        if stab_tests is None:
            self.tests = self.num_nodes
        elif stab_tests > (2 ** self.num_nodes):
            raise ValueError(f"Number of stabilizers to be tested must be less than {2 ** self.num_nodes}")
        else:
            self.tests = stab_tests
        self.ntotal = 2 * self.tests * self.ntest

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
        # Preparation phase
        ###

        # Generate list of indices referring to copies of the GHZ state
        copies = list(range(self.ntotal))
        logger.warning(f"Total GHZ copies: {self.ntotal}")

        # Generate full set of stabilizers
        stabilizers = gen_stabilizer_set(self.num_nodes)
        stab_names = list(stabilizers.keys())
        logger.warning(f"Complete set of stabilizers: {stab_names}")

        # Randomly select specified number of stabilizers to test
        stab_names = random.sample(stab_names, self.tests)
        bases = [stabilizers[s] for s in stab_names]
        logger.warning(f"Stabilizers selected for measurement: {stab_names}")


        # Initialize list of copy groups
        copy_groups = []

        # Randomly select ntest copies to measure each stabilizer
        for _ in range(self.tests):
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

        # Variable to hold target qubit
        target_qubit = None

        # Variable to hold measurement results
        results = []
        for s in range(self.tests):
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

            # Default action if copy index is not in one of the selected groups
            qubit_action = "discard"

            ## Identify action to be performed on qubit ##
            # Check which copy group the current copy is in
            for i in range(self.tests+1):
                # Last copy group contains only the target index
                if i == self.tests and c in copy_groups[i]:
                    qubit_action = "keep"
                    break
                # Otherwise, group i contains copy indices to measure w.r.t. stabilizer K_i+1
                elif c in copy_groups[i]:
                    qubit_action = "measure"
                    # Get the corresponding stabilizer
                    test_number = copy_groups[i].index(c)
                    stab_bases = bases[i]
                    stab_number = i
                    break

            logger.warning(f"Copy: {c}, qubit action: {qubit_action}")

            if qubit_action == "measure":
                logger.warning(f"Measurement: {stab_bases}")

                # Get measurement basis for the verifier node and measure the qubit
                basis = stab_bases[verifier_id]
                logger.warning(f"{self.name} will measure in {basis} basis")

                if basis == 'Y':    # Y measurement
                    qubit.K()
                elif basis == 'X':  # X measurement
                    qubit.H()
                # Otherwise standard Z measurement
                
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
        for j in range(self.tests):
            measurements = np.array(results[j])
            stab = stab_names[j]
            stab_bases = bases[j]
            logger.warning(f"Measurement bases: {stab_bases}")

            # Identify nodes measuring Identity
            iden_nodes = []
            for i in range(len(stab_bases)):
                    if stab_bases[i] == 'I':
                        iden_nodes.append(i)
            
            num_failures = 0
            logger.warning(f"Results taken into account:")
            for test in measurements:
                test = np.delete(test, iden_nodes)
                logger.warning(test)
                parity = np.prod(test)
                if str.startswith(stab, "-"):
                    parity *= -1
                if parity == -1:
                    num_failures += 1
            failure_rate = num_failures / self.ntest
            failure_rates.append(failure_rate)
            logger.warning(f"Failure rate: {failure_rate}\n")

        avg_failure_rate = np.mean(failure_rates)
        logger.warning(f"Average failure rate: {avg_failure_rate}")

        return {"name": self.name, 
                "failure rates": failure_rates,
                "average failure rate": avg_failure_rate,
                "target qubit": target_qubit,
                "target index": target}
    

###
#   This class defines the program run by the Verifier node of the quantum network.
#   As of now, the first node in node_names is automatically selected as the Verifier.
#
#   In the run method, we divide the protocol into two phases:
#
#       Preparation phase:
#       1.  The node identifies its neighboring nodes for the GHZ state creation.
#       2.  It initializes variables to hold the target qubit and the qubits to be discarded
#       3.  Before starting the state distrubution, the node establishes classical communication 
#           channels with the Verifier.
#
#       GHZ distribution and measurement phase:
#
#       The following steps 1-3 are performed ntotal times
#       1.  Generate a GHZ state with the other nodes in the network using 'create_ghz()'.
#       2.  The node receives the message from the Verifier indicating the action to perform on the qubit.
#       3a. If qubit action = discard, the node marks its qubit for deletion.
#       3b. If qubit action = measure,
#           1.  The node receives the message from the Verifier indicating its measurement basis.
#           2.  It measures its qubit accordingly and sends the result to the Verifier.
#       3c. If qubit action = keep, the node stores its qubit as the target qubit.
#
#       4.  The node discards its unused qubits from memory.
#       5.  The node outputs its target qubit.
###
class GHZMemberNode_select(Program):
    def __init__(self, name:str, node_names:List[str], ntest:int, stab_tests:int):
        self.name = name
        self.node_names = node_names
        self.peer_names = [peer for peer in self.node_names if peer != self.name]
        self.num_nodes = len(self.node_names)
        self.ntest = ntest
        if stab_tests is None:
            self.tests = self.num_nodes
        elif stab_tests > (2 ** self.num_nodes):
            raise ValueError(f"Number of stabilizers to be tested must be less than {2 ** self.num_nodes}")
        else:
            self.tests = stab_tests
        self.ntotal = 2 * self.tests * self.ntest

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

        # Variable to hold target qubit
        target_qubit = None

        # Establish classical connection with Verifier node
        csocket = context.csockets[self.node_names[0]]

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

                if basis == 'Y':    # Y measurement
                    qubit.K()
                elif basis == 'X':  # X measurement
                    qubit.H()
                # Otherwise standard Z measurement
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
            
        # Last node will output the density matrix of the shared target copy 
        if self.name == self.node_names[-1]:
            full_state = get_qubit_state(target_qubit, self.name, full_state=True)
            logger.warning(f"Outputting density matrix of shared state")
            return {"name": self.name, 
                    "target qubit": target_qubit,
                    "full state": full_state}
        # Others will just return their qubit of the unmeasured target copy
        else:
            return {"name": self.name, "target qubit": target_qubit}

def gen_stabilizer_set(num_nodes: int):
    # Get generator for the set of stabilizers
    stab_dict = get_generators(num_nodes)
    generators = list(stab_dict.keys())
    #print(f"Generators: \n{generators}")
 
    stab_dict['I'*num_nodes] = ['I' for i in range(num_nodes)]
    product_stabs = []
    for i in range(2, num_nodes+1):
        products = combinations(generators, i)
        for tup in products:
            #print(tup)
            product_stabs.append(stabilizer_product(tup, num_nodes))
            #print(product_stabs[-1])
    
    for stab in product_stabs:
        bases = []
        for letter in stab[-num_nodes:]:
            bases.append(letter)
            stab_dict[stab] = bases
    
    return stab_dict

def stabilizer_product(tup: tuple, num_nodes: int):
    sign_exp = 0
    stabs = []
    for s in tup:
        if s[0] == '-':
            sign_exp += 1
        stabs.append(s[-num_nodes:])
    #print(f"Initial sign: {(-1)**sign_exp}")
    #print(stabs)

    result = ''
    for i in range(num_nodes):
        paulis = [s[i] for s in stabs]
        prod, sign_count = pauli_product(paulis)
        sign_exp = (sign_exp + sign_count) % 2
        #print(f"Paulis: {paulis} \tProduct: {prod}")
        #print(f"Updated sign: {(-1)**sign_exp}")
        if prod == 0:
            result += 'I'
        elif prod == 1:
            result += 'X'
        elif prod == 2:
            result += 'Y'
        else:
            result += 'Z'
    
    sign = (-1)**sign_exp
    if sign < 0:
        result = '-' + result

    return result


def pauli_product(paulis: List[str]):
    paulis_int = []
    sign_count = 0
    i_count = 0
    for pauli in paulis:
        if pauli == 'X':
            paulis_int.append(1) # Encoding for X
        if pauli == 'Y':
            paulis_int.append(2) # Encoding for Y

    # Encoding for Z will be 3 and I will 0
    
    # Variable to track current product as we loop through the Paulis
    result = 0

    for i in paulis_int:
        if i == result:     # XX, YY, ZZ = I
            result = 0
        elif result == 0:   # IS = S for all S
            result = i  
        elif (result - i) == 2:   # ZX = iY
            i_count += 1
            result = 2
        else:   # XY = iZ, YX = -iZ, ZY = -iX (XZ or YZ would never occur)
            if i < result: # YX or ZY
                sign_count += 1
            i_count += 1
            result = (result + i) % 4
            
    sign_count += (i_count / 2)
    return result, sign_count

if __name__ == '__main__':
    stabilizers = gen_stabilizer_set(4)
    pprint(stabilizers)


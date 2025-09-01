from itertools import combinations
from typing import Dict, List
from pprint import pprint
import random
import numpy as np
import cmath
from collections import deque

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

class SensingProgram_verifier(Program):
    def __init__(self, name:str, node_names:List[str], phase:float, ntest:int, copies:int, failure_threshold:float, send_state:bool=False):
        self.name = name
        self.node_names = node_names
        self.peer_names = [peer for peer in self.node_names if peer != self.name]
        self.num_nodes = len(self.node_names)
        self.tests = ntest
        if copies > ntest:
            self.ntotal = copies
        else:
            raise ValueError("Number of copies must be greater than number of tests")
        self.target_qubit = None
        self.avg_failure_rate = None
        self.failure_threshold = failure_threshold
        self.phase = phase
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
        logger.warning(f"Total GHZ copies: {self.ntotal}")
        logger.warning(f"Total tests: {self.tests}")

        # Generate list of stabilizers
        stabilizers = gen_stabilizer_set(self.num_nodes)
        stab_names = list(stabilizers.keys())
        logger.warning(f"Stabilizers: {stab_names}")
        
        # Select target copy and remove it from copies
        target_idx = random.choice(copies)
        copies.remove(target_idx)
        logger.warning(f"Target copy: {target_idx}")

        # Randomly select ntest copies to be tested, each with a random stabilizer
        test_copies = random.sample(copies, self.tests)
        test_map = {}
        logger.warning(f"Stabilizer tests")
        for t in test_copies:
            test_map[t] = random.choice(stab_names)
            logger.warning(f"Copy {t}: {test_map[t]}")

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
        results = [[-1] * self.num_nodes for s in range(self.tests)]

        # Establish classical connections to all member nodes
        csockets = [context.csockets[peer] for peer in self.peer_names]

        ### 
        # GHZ distribution and measurement phase
        ###

        # Variable to hold queue of tested stabilizers
        stab_tests = deque()

        # Test counter
        test_count = 0

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

            # Determine action to be performed on copy
            if c == target_idx:
                qubit_action = "keep"  
            elif c in test_map:
                qubit_action = "measure"
            else:
                qubit_action = "discard"
            
            logger.warning(f"Copy: {c}, qubit action: {qubit_action}")

            if qubit_action == "measure":
                test_count += 1

                # Randomly choose stabilizer to be tested on copy and store it in queue #
                stab_name = test_map[c]
                stab_tests.append(stab_name)
                stab_bases = stabilizers[stab_name]
                logger.warning(f"Measurement: {stab_bases}")

                # Get measurement basis for the verifier node and measure the qubit
                basis = stab_bases[verifier_id]
                logger.warning(f"{self.name} will measure in {basis} basis")

                if basis == 'I':            # I measurement (always +1 outcome)
                    m = 0
                else:
                    if basis == 'Y':        # Y measurement
                        qubit.K()
                    elif basis == 'X':      # X measurement
                        qubit.H()
                
                    m = qubit.measure()     # standard Z measurement
                    yield from connection.flush()

                # Store eigenvalue result in appropriate location
                logger.debug(f"Measured result {int(m)}")
                results[test_count-1][verifier_id] **= int(m)

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
                    results[test_count-1][node_index] **= m
            
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

        num_failures = 0
        # Calculate failure rate for each stabilizer measurement
        for j in range(self.tests):
            measurements = np.array(results[j])
            stab_name = stab_tests.popleft()
            bases = stabilizers[stab_name]
            logger.warning(f"Measurement bases: {bases}")

            logger.warning(f"Results:")
            #measurements = np.delete(measurements, iden_nodes)
            logger.warning(measurements)
            parity = np.prod(measurements)
            if str.startswith(stab_name, "-"):
                parity *= -1
            if parity == -1:
                num_failures += 1
                
        self.avg_failure_rate = num_failures / self.tests
        logger.warning(f"Average failure rate: {self.avg_failure_rate}")
    
    def run(self, context: ProgramContext):
        connection = context.connection
        logger = LogManager.get_stack_logger(f"{self.name}_Verifier")

        # Establish classical connections to all member nodes
        csockets = [context.csockets[peer] for peer in self.peer_names]

        # Run verification protocol
        yield from self._run_verification(context, csockets)
        
        #f_threshold = 1 / (2 * self.num_nodes**2)
        logger.warning(f"Threshold failure rate is {self.failure_threshold}")

        # If failure rate below threshold
        if self.avg_failure_rate < self.failure_threshold:
            logger.warning(f"Average failure rate below threshold. Continuing with sensing.")
            # Inform all other nodes to continue with sensing
            for csocket in csockets:
                csocket.send("continue")
            
            # Encode the phase onto target qubit
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
                        "status": 0}
            
            else:
                logger.warning(f"Outputting unmeasured qubit")
                return {"name": self.name,
                        "average failure rate": self.avg_failure_rate,
                        "qubit": self.target_qubit,
                        "status": 0}

        else:   # Otherwise abort the protocol
            logger.warning(f"Average failure rate not below threshold. Aborting protocol.")
            for csocket in csockets:
                csocket.send("abort")
            return {"name": self.name, 
                    "average failure rate": self.avg_failure_rate,
                    "status": 1}

    
class SensingProgram_member(Program):
    def __init__(self, name:str, node_names:List[str], phase:float, ntest:int, copies:int, send_state:bool=False):
        self.name = name
        self.node_names = node_names
        self.peer_names = [peer for peer in self.node_names if peer != self.name]
        self.num_nodes = len(self.node_names)
        self.tests = ntest
        if copies > ntest:
            self.ntotal = copies
        else:
            raise ValueError("Number of copies must be greater than number of tests")
        self.target_qubit = None
        self.phase = phase
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

                if basis == 'I':            # I measurement (always +1 outcome)
                    m = 0
                else:
                    if basis == 'Y':        # Y measurement
                        qubit.K()
                    elif basis == 'X':      # X measurement
                        qubit.H()
                
                    m = qubit.measure()     # standard Z measurement
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

        #return {"name": self.name, "target qubit": self.target_qubit}
    
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
                        "parity": (-1)**int(m)}
            
            else:
                # Last node will output the density matrix of the shared state
                if self.name == self.node_names[-1]:
                    full_state = get_qubit_state(self.target_qubit, self.name, full_state=True)
                    logger.warning(f"Outputting density matrix of shared state")
                    return {"name": self.name,
                            "qubit": self.target_qubit, 
                            "full state": full_state}

                else:
                    logger.warning(f"Outputting unmeasured qubit")
                    return {"name": self.name, 
                            "qubit": self.target_qubit}
        
        else:
            logger.warning(f"Sensing protocol aborted")
            return {"name": self.name}
        
class SensingProgram_member_bitflip(Program):
    def __init__(self, name:str, node_names:List[str], phase:float, ntest:int, copies:int, send_state:bool=False):
        self.name = name
        self.node_names = node_names
        self.peer_names = [peer for peer in self.node_names if peer != self.name]
        self.num_nodes = len(self.node_names)
        self.tests = ntest
        if copies > ntest:
            self.ntotal = copies
        else:
            raise ValueError("Number of copies must be greater than number of tests")
        self.target_qubit = None
        self.phase = phase
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

                if basis == 'I':            # I measurement (always +1 outcome)
                    m = 0
                else:
                    if basis == 'Y':        # Y measurement
                        qubit.K()
                    elif basis == 'X':      # X measurement
                        qubit.H()
                
                    m = qubit.measure()     # standard Z measurement
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

        #return {"name": self.name, "target qubit": self.target_qubit}
    
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
            # Simulate bit flip on the node's qubit
            self.target_qubit.X()

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
                        "parity": (-1)**int(m)}
            
            else:
                # Last node will output the density matrix of the shared state
                if self.name == self.node_names[-1]:
                    full_state = get_qubit_state(self.target_qubit, self.name, full_state=True)
                    logger.warning(f"Outputting density matrix of shared state")
                    return {"name": self.name,
                            "qubit": self.target_qubit, 
                            "full state": full_state}

                else:
                    logger.warning(f"Outputting unmeasured qubit")
                    return {"name": self.name, 
                            "qubit": self.target_qubit}
        
        else:
            logger.warning(f"Sensing protocol aborted")
            return {"name": self.name}


###
#   Generates the full set of stabilizers of a GHZ state
#   Input : n - number of nodes in the network
#   Uses get_generators() to output a list of strings representing the generator set using X and Y Paulis
#   Uses stabilizer_product() to calculate the product of a chosen combination of stabilizers
#   Output : dictionary containing the strings representing the full set of stabilizers
###
def gen_stabilizer_set(num_nodes: int):
    # Get generator for the set of stabilizers
    stab_dict = get_generators(num_nodes)
    generators = list(stab_dict.keys())
    #print(f"Generators: \n{generators}")
 
    stab_dict['I'*num_nodes] = ['I' for i in range(num_nodes)]
    product_stabs = []
    # Get all possible 2, 3, ..., n-combinations of the stabilizers in the generator set
    for i in range(2, num_nodes+1):
        combos = combinations(generators, i)
        # For each combination, calculate the product of the chosen stabilizers
        for tup in combos:
            product_stabs.append(stabilizer_product(tup, num_nodes))
    
    for stab in product_stabs:
        bases = []
        for letter in stab[-num_nodes:]:
            bases.append(letter)
            stab_dict[stab] = bases
    
    return stab_dict


###
#   Calculates the product of multiple independent stabilizers of the GHZ state
#   Input : tuple containing the stabilizers to be multiplied and the number of nodes
#   e.g. (-XXYY, -XYYX, XXXX), 4
#   Uses pauli_product() to calculate the product for each node
#   Outputs a string representing the resulting stabilizer
###
def stabilizer_product(tup: tuple, num_nodes: int):
    # Variable to keep track of the number of -1 that appear in the product
    sign_exp = 0
    stabs = []
    for s in tup:
        if s[0] == '-':
            sign_exp += 1
        stabs.append(s[-num_nodes:])

    result = ''
    # For each node
    for i in range(num_nodes):
        # Calculate the pauli product
        paulis = [s[i] for s in stabs]
        prod, sign_count = pauli_product(paulis)
        # Account for the sign of the product
        sign_exp = (sign_exp + sign_count) % 2
        # Decode the product to output strings
        if prod == 0:
            result += 'I'
        elif prod == 1:
            result += 'X'
        elif prod == 2:
            result += 'Y'
        else:
            result += 'Z'
    
    # Calculate the sign
    sign = (-1)**sign_exp
    if sign < 0:
        result = '-' + result

    return result

###
#   Calculates the product of single qubit Paulis from a given list
#   Note - Since our generator set only consists of X and Y, this function is only defined to account for
#   an input list containing X and Y
#   Outputs an integer representing I, X, Y or Z 
#   and a count of the -1 that appeared during the multiplication
###
def pauli_product(paulis: List[str]):
    paulis_int = []
    # Variable to keep track of all the -1
    sign_count = 0
    # Variable to keep track of all the i that appear
    i_count = 0
    # Convert the input string list into an integer list
    for pauli in paulis:
        if pauli == 'X':
            paulis_int.append(1) # Encoding for X
        if pauli == 'Y':
            paulis_int.append(2) # Encoding for Y
    # Encoding for Z will be 3 and I will 0
    
    # Variable to track current product as we loop through the Paulis in the input list
    result = 0

    # Loop through the Paulis and calculate the possible products
    for i in paulis_int:
        if i == result:     # XX, YY, ZZ = I
            result = 0
        elif result == 0:   # IS = S for all S
            result = i  
        elif (result - i) == 2:   # ZX = iY
            i_count += 1
            result = 2
        else:   # XY = iZ, YX = -iZ, ZY = -iX (XZ or YZ would never occur since no Z in input)
            if i < result: # YX or ZY
                sign_count += 1
            i_count += 1
            result = (result + i) % 4
    
    # We pick up a -1 for every 2 i
    sign_count += (i_count / 2)

    return result, sign_count

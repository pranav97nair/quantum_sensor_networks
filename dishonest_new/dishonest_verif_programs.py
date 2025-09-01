from collections import deque
from typing import Dict, List
from itertools import combinations
from pprint import pprint
import random
import numpy as np
import gc

from squidasm.sim.stack.program import Program, ProgramContext, ProgramMeta # type: ignore
from squidasm.sim.stack.common import LogManager # type: ignore
from squidasm.util.routines import create_ghz # type: ignore
from squidasm.util.util import get_qubit_state # type: ignore
#from verification_programs_full import *

class DishonestNode_applyZ(Program):
    def __init__(self, name:str, node_names:List[str], ntest:int, copies:int):
        self.name = name
        self.node_names = node_names
        self.peer_names = [peer for peer in self.node_names if peer != self.name]
        self.num_nodes = len(self.node_names)
        self.tests = ntest
        if copies > ntest:
            self.ntotal = copies
        else:
            raise ValueError("Number of copies must be greater than number of tests")

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

            # Dishonest action - apply Pauli Z to qubit
            qubit.Z()
            
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
        
class DishonestNode_applyX(Program):
    def __init__(self, name:str, node_names:List[str], ntest:int, copies:int):
        self.name = name
        self.node_names = node_names
        self.peer_names = [peer for peer in self.node_names if peer != self.name]
        self.num_nodes = len(self.node_names)
        self.tests = ntest
        if copies > ntest:
            self.ntotal = copies
        else:
            raise ValueError("Number of copies must be greater than number of tests")

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

            # Dishonest action - apply Pauli X to qubit
            qubit.X()
            
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
        

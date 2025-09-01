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

class DishonestSensing_applyZ(Program):
    def __init__(self, name:str, node_names:List[str], ntest:int, copies:int, send_state:bool=False):
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
            # Dishonest action, apply phase flip
            self.target_qubit.Z()

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
        

class DishonestSensing_applyX(Program):
    def __init__(self, name:str, node_names:List[str], ntest:int, copies:int, send_state:bool=False):
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
            # Dishonest action, apply bit flip
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
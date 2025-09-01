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


class GHZSensingProgram(Program):
    def __init__(self, name:str, node_names:List[str]):
        self.name = name
        self.node_names = node_names
        self.peer_names = [peer for peer in self.node_names if peer != self.name]
        self.target_qubit = None
        self.phase = random.uniform(0, np.pi)

    @property
    def meta(self) -> ProgramMeta:
        return ProgramMeta(
            name="GHZSensingProgram",
            csockets=self.peer_names,
            epr_sockets=self.peer_names,
            max_qubits=2
        )

    def run(self, context: ProgramContext):
        connection = context.connection
        logger = LogManager.get_stack_logger(f"{self.name}")

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

        ## Generate one GHZ state and receive assigned qubit ##
        self.target_qubit, _ = yield from create_ghz(
                connection,
                down_epr_socket,
                up_epr_socket,
                down_socket,
                up_socket,
                do_corrections=True
            )

        ## Carry out sensing protocol ##
        logger.warning(f"GHZ qubit received. Continuing with sensing.")
        
        # Encode the phase onto target qubit
        logger.warning(f"{self.name} has phase {self.phase}")
        #self.phase = 0         # to test applying no rotation
        self.target_qubit.rot_Z(angle=self.phase)          

        # Measure qubit in X basis
        self.target_qubit.H()
        m = self.target_qubit.measure()

        subroutine = connection.compile()
        yield from connection.commit_subroutine(subroutine)

        logger.warning(f"{self.name} measured {int(m)}")

        return {"name": self.name,
                "parity": (-1)**int(m),
                "local phase": self.phase}


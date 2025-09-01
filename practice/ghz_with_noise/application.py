from typing import List

from squidasm.sim.stack.program import Program, ProgramContext, ProgramMeta # type: ignore
from squidasm.util.routines import create_ghz # type: ignore

from squidasm.util.util import get_qubit_state # type: ignore

class GHZProgram(Program):
    def __init__(self, name: str, node_names: List[str]):
        self.name = name
        self.node_names = node_names
        self.peer_names = [peer for peer in self.node_names if peer != self.name]

    @property
    def meta(self) -> ProgramMeta:
        return ProgramMeta(
            name="test_program",
            csockets=self.peer_names,
            epr_sockets=self.peer_names,
            max_qubits=2,
        )
        
    def run(self, context: ProgramContext):
        connection = context.connection
        #print(f"Running {self.name} node...")

        # Find the index of current node
        i = self.node_names.index(self.name)
        down_epr_socket = None
        up_epr_socket = None
        down_socket = None
        up_socket = None

        if i > 0:
            down_name = self.node_names[i - 1]
            #print(f"Down node : {down_name}")
            down_epr_socket = context.epr_sockets[down_name]
            down_socket = context.csockets[down_name]
        if i < len(self.node_names) - 1:
            up_name = self.node_names[i + 1]
            #print(f"Up node : {up_name}")
            up_epr_socket = context.epr_sockets[up_name]
            up_socket = context.csockets[up_name]

        qubit, _ = yield from create_ghz(
            connection,
            down_epr_socket,
            up_epr_socket,
            down_socket,
            up_socket,
            do_corrections=True
        )
        
        q_measure = qubit.measure()
        yield from connection.flush()

        return {"name": self.name, "result": int(q_measure)}
    
class GHZProgram_send_states(Program):
    def __init__(self, name: str, node_names: List[str]):
        self.name = name
        self.node_names = node_names
        self.peer_names = [peer for peer in self.node_names if peer != self.name]

    @property
    def meta(self) -> ProgramMeta:
        return ProgramMeta(
            name="test_program",
            csockets=self.peer_names,
            epr_sockets=self.peer_names,
            max_qubits=2,
        )
        
    def run(self, context: ProgramContext):
        connection = context.connection
        #print(f"Running {self.name} node...")

        # Find the index of current node
        i = self.node_names.index(self.name)
        down_epr_socket = None
        up_epr_socket = None
        down_socket = None
        up_socket = None

        if i > 0:
            down_name = self.node_names[i - 1]
            #print(f"Down node : {down_name}")
            down_epr_socket = context.epr_sockets[down_name]
            down_socket = context.csockets[down_name]
        if i < len(self.node_names) - 1:
            up_name = self.node_names[i + 1]
            #print(f"Up node : {up_name}")
            up_epr_socket = context.epr_sockets[up_name]
            up_socket = context.csockets[up_name]

        qubit, _ = yield from create_ghz(
            connection,
            down_epr_socket,
            up_epr_socket,
            down_socket,
            up_socket,
            do_corrections=True
        )
        
        yield from connection.flush()
        state = get_qubit_state(qubit, self.name)
        if i == len(self.node_names) - 1:
            full_state = get_qubit_state(qubit, self.name, full_state=True)
        else:
            full_state = None

        return {"name": self.name, "state": [state, full_state]}

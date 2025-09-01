import random
from typing import List

from squidasm.sim.stack.program import Program, ProgramContext, ProgramMeta # type: ignore
from squidasm.util.routines import create_ghz # type: ignore
from netqasm.sdk.qubit import QubitMeasureBasis

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
        
        #print(f"Qubit state: {get_qubit_state(qubit, self.name)}")
        q_measure = qubit.measure()
        yield from connection.flush()

        return {"name": self.name, "result": int(q_measure)}
    
class GHZProgram_send_reduc_states(Program):
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

        return {"name": self.name, "state": state}

class GHZProgram_send_full_state(Program):
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

        # Identify the down and up nodes
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
        full_state = (
            get_qubit_state(qubit, self.name, full_state=True)
            if i == len(self.node_names) - 1 else None
        )

        return {"name": self.name, "state": full_state}
    
class GHZProgram_multi(Program):
    def __init__(self, name: str, node_names: List[str], num_copies: int=1):
        self.name = name
        self.node_names = node_names
        self.peer_names = [peer for peer in self.node_names if peer != self.name]
        self.num_copies = num_copies

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

        # Identify the down and up nodes
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

        measurements = []
        for c in range(self.num_copies):
            qubit, _ = yield from create_ghz(
                connection,
                down_epr_socket,
                up_epr_socket,
                down_socket,
                up_socket,
                do_corrections=True
            )
            #print(f"Qubit state: {get_qubit_state(qubit, self.name)}")
            q_measure = qubit.measure()
            measurements.append(q_measure)
            yield from connection.flush()
        
        measurements = [int(m) for m in measurements]
        return {"name": self.name, "measurements": measurements}
    
class GHZProgram_measureX(Program):
    def __init__(self, name: str, node_names: List[str], ntotal: int=1):
        self.name = name
        self.node_names = node_names
        self.peer_names = [peer for peer in self.node_names if peer != self.name]
        self.ntotal = ntotal

    @property
    def meta(self) -> ProgramMeta:
        return ProgramMeta(
            name="GHZStabilizer",
            csockets=self.peer_names,
            epr_sockets=self.peer_names,
            max_qubits=2,
        )
    
    def run(self, context: ProgramContext):
        connection = context.connection

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
        
        measurements = []
        # Get the appropriate qubit from each of the ntotal GHZ states
        for c in range(self.ntotal):
            qubit, _ = yield from create_ghz(
                connection,
                down_epr_socket,
                up_epr_socket,
                down_socket,
                up_socket,
                do_corrections=True
            )

            # Measure every qubit in the X basis
            qubit.H()
            q_measure = qubit.measure()
            measurements.append(q_measure)
            yield from connection.flush()

        measurements = [int(m) for m in measurements]
        return {"name": self.name, "measurements": measurements}

class GHZProgram_select_measureX(Program):
    def __init__(self, name: str, node_names: List[str], ntest: int):
        self.name = name
        self.node_names = node_names
        self.peer_names = [peer for peer in self.node_names if peer != self.name]
        self.ntest = ntest
        self.ntotal = 2 * self.ntest * len(self.node_names)

    @property
    def meta(self) -> ProgramMeta:
        return ProgramMeta(
            name="GHZStabilizer",
            csockets=self.peer_names,
            epr_sockets=self.peer_names,
            max_qubits=2,
        )
    
    def run(self, context: ProgramContext):
        connection = context.connection

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
        
        # Select copies to measure
        copies = range(self.ntotal)
        measure_copies = random.sample(copies, self.ntest)

        measurements = []
        remaining_qubits = []
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

            if c in measure_copies:
                qubit.H()
                q_measure = qubit.measure()
                measurements.append(q_measure)
            else:
                measurements.append(None)
                remaining_qubits.append(qubit)

            yield from connection.flush()

        measurements = list(
            int(m) if m is not None 
            else None
            for m in measurements
        )
        return {"name": self.name, "measurements": measurements, "qubits": remaining_qubits}
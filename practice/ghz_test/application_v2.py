from enum import Enum, auto
from typing import Generator, Optional, Tuple, List

from netqasm.sdk import EPRSocket
from netqasm.sdk.classical_communication.socket import Socket
from netqasm.sdk.connection import BaseNetQASMConnection
from netqasm.sdk.qubit import Qubit

from squidasm.sim.stack.program import ProgramContext, Program, ProgramMeta # type: ignore
from squidasm.util.util import get_qubit_state # type: ignore

class _Role(Enum):
    start = auto()
    middle = auto()
    end = auto()

def create_ghz(
    connection: BaseNetQASMConnection,
    down_epr_socket: Optional[EPRSocket] = None,
    up_epr_socket: Optional[EPRSocket] = None,
    down_socket: Optional[Socket] = None,
    up_socket: Optional[Socket] = None,
    do_corrections: bool = False,
) -> Generator[None, None, Tuple[Qubit, int]]:
    r"""Local protocol to create a GHZ state between multiples nodes.

    EPR pairs are generated in a line and turned into a GHZ state by performing half of a Bell measurement.
    That is, CNOT and H are applied but only the control qubit is measured.
    If `do_corrections=False` (default) this measurement outcome is returned along with the qubit to be able to know
    what corrections might need to be applied.
    If the node is at the start or end of the line, the measurement outcome 0 is always returned since there
    is no measurement performed.
    The measurement outcome indicates if the next node in the line should flip its qubit to get the standard
    GHZ state: :math:`|0\rangle^{\otimes n} + |1\rangle^{\otimes n}`.

    On the other hand if `do_corrections=True`, then the classical sockets `down_socket` and/or `up_socket`
    will be used to communicate the outcomes and automatically perform the corrections.

    Depending on if down_epr_socket and/or up_epr_socket is specified the node,
    either takes the role of the:

    * "start", which initialises the process and creates an EPR
      with the next node using the `up_epr_socket`.
    * "middle", which receives an EPR pair on the `down_epr_socket` and then
      creates one on the `up_epr_socket`.
    * "end", which receives an EPR pair on the `down_epr_socket`.

    .. note::
        There has to be exactly one "start" and exactly one "end" but zero or more "middle".
        Both `down_epr_socket` and `up_epr_socket` cannot be `None`.

    :param connection: The connection to the quantum node controller used for sending instructions.
    :param down_epr_socket: The EPRSocket to be used for receiving EPR pairs from downstream.
    :param up_epr_socket: The EPRSocket to be used for create EPR pairs upstream.
    :param down_socket: The classical socket to be used for sending corrections, if `do_corrections = True`.
    :param up_socket: The classical socket to be used for sending corrections, if `do_corrections = True`.
    :param do_corrections: If corrections should be applied to make the GHZ in the standard form
        :math:`|0\rangle^{\otimes n} + |1\rangle^{\otimes n}` or not.
    :return: Of the form `(q, m)` where `q` is the qubit part of the state and `m` is the measurement outcome.
    """
    if down_epr_socket is None and up_epr_socket is None:
        raise TypeError("Both down_epr_socket and up_epr_socket cannot be None")

    if down_epr_socket is None:
        # Start role
        role = _Role.start
        yield from up_socket.recv()
        q = up_epr_socket.create_keep()[0]
        m = 0
    else:
        down_socket.send("")
        q = down_epr_socket.recv_keep()[0]
        if up_epr_socket is None:
            # End role
            role = _Role.end
            m = 0
        else:
            # Middle role
            role = _Role.middle

            yield from up_socket.recv()

            q_up: Qubit = up_epr_socket.create_keep()[0]  # type: ignore
            # merge the states by doing half a Bell measurement
            q.cnot(q_up)
            m = q_up.measure()

    # Flush the subroutine
    subroutine = connection.compile()
    yield from connection.commit_subroutine(subroutine)
    
    if do_corrections:
        if role == _Role.start:
            assert up_socket is not None
            up_socket.send(str(0))
        else:
            assert down_socket is not None
            corr = yield from down_socket.recv()
            assert isinstance(corr, str)
            corr = int(corr)
            if corr == 1:
                q.X()
            if role == _Role.middle:
                assert up_socket is not None
                corr = (corr + m) % 2
                up_socket.send(str(corr))
        # Reflush subroutine to implement corrections if needed
        subroutine = connection.compile()
        yield from connection.commit_subroutine(subroutine)
        m = 0

    return q, int(m)


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
        connection : BaseNetQASMConnection = context.connection
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

        # Execute GHZ creation subroutine
        qubit, _ = yield from create_ghz(
            connection,
            down_epr_socket,
            up_epr_socket,
            down_socket,
            up_socket,
            do_corrections=True
        )
        
        full_state = (
            get_qubit_state(qubit, self.name, full_state=True)
            if i == len(self.node_names) - 1 else None
        )

        return {"name": self.name, "state": full_state}
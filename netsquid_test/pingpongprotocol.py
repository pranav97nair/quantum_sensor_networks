import netsquid as ns
from netsquid.protocols import NodeProtocol

class PingPongProtocol(NodeProtocol):
    def __init__(self, node, observable, qubit=None):
        super().__init__(node)
        self.observable = observable
        self.qubit = qubit
        # Define matching pair of strings for pretty printing of basis states
        self.basis = ["|0>", "|1>"] if observable ==ns.Z else ["|+>", "|->"]

    def run(self):
        if self.qubit is not None:
            # Send (TX) qubit to the other node via port's output:
            self.node.ports["qubitIO"].tx_output(self.qubit)
        while True:
            # Wait (yield) until input has arrived on our port:
            yield self.await_port_input(self.node.ports["qubitIO"])
            # Receive (RX) qubit on the port's input:
            message = self.node.ports["qubitIO"].rx_input()
            qubit = message.items[0]
            meas, prob = ns.qubits.measure(qubit, observable=self.observable)
            print(f"{ns.sim_time():5.1f}: {self.node.name} measured "
                  f"{self.basis[meas]} with probability {prob:.2f}")
            # Send (TX) qubit to the other node via connection:
            self.node.ports["qubitIO"].tx_output(qubit)


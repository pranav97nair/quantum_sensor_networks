import netsquid as ns
import netsquid.qubits as nsq
from netsquid.nodes import Node, DirectConnection
from pingpongdelay import PingPongDelayModel # type: ignore
from pingpongprotocol import PingPongProtocol # type: ignore
from netsquid.components import QuantumChannel

node_ping = Node(name="Ping")
node_pong = Node(name="Pong")

distance = 2.74 / 1000 # default unit of length in channels is km
delay_model = PingPongDelayModel()
channel_1 = QuantumChannel(name="qchannel[ping to pong]", 
                           length=distance, 
                           models={"delay_model": delay_model})
channel_2 = QuantumChannel(name="qchannel[pong to ping]", 
                           length=distance, 
                           models={"delay_model": delay_model})

connection = DirectConnection(name="conn[ping|pong]",
                              channel_AtoB=channel_1,
                              channel_BtoA=channel_2)
node_ping.connect_to(remote_node=node_pong, connection=connection,
                     local_port_name="qubitIO", remote_port_name="qubitIO")

qubits = nsq.create_qubits(1)
ping_protocol = PingPongProtocol(node_ping, observable=ns.Z, qubit=qubits[0])
pong_protocol = PingPongProtocol(node_pong, observable=ns.X)

ping_protocol.start()
pong_protocol.start()
run_stats = ns.sim_run(duration=300)
print(run_stats)


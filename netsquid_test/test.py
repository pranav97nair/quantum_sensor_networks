import netsquid as ns
import netsquid.qubits as nsq

qubits = nsq.create_qubits(1)
#print(qubits)

qubit = qubits[0]
# Density matrix - should be in |0> state
dm = nsq.reduced_dm(qubit)
#print(dm)

nsq.operate(qubit, ns.X)
# Now dm should be in |1> state
dm = nsq.reduced_dm(qubit)
#print(dm)

# Measure qubit in X basis
m, prob = nsq.measure(qubit, observable=ns.X)
if m == 0:
    state = "|+>"
else:
    state = "|->"
print(f"Measured {state} with probability {prob:.1f}")

dm = nsq.reduced_dm(qubit)
print(dm)
import numpy as np
from application import AliceProgram, BobProgram

from squidasm.run.stack.config import StackNetworkConfig # type: ignore
from squidasm.run.stack.run import run # type: ignore

cfg = StackNetworkConfig.from_file("config.yaml")

epr_rounds = 10
alice_program = AliceProgram(num_epr_rounds=epr_rounds)
bob_program = BobProgram(num_epr_rounds=epr_rounds)

simulation_iterations = 20
results_alice, results_bob = run(
    config = cfg,
    programs = {"Alice": alice_program, "Bob": bob_program},
    num_times=simulation_iterations
)

results_alice = [results_alice[i]["measurements"] for i in range(simulation_iterations)]
results_bob = [results_bob[i]["measurements"] for i in range(simulation_iterations)]

results_alice = np.concatenate(results_alice).flatten()
results_bob = np.concatenate(results_bob).flatten()

errors = [
    result_alice != result_bob
    for result_alice, result_bob in zip(results_alice, results_bob)
]

print(f"average error rate: {sum(errors) / len(errors) * 100:.1f}% using {len(errors)} epr requests")
print(f"average value Alice: {sum(results_alice) / len(results_alice)}")
print(f"average value Bob: {sum(results_bob) / len(results_bob)}")

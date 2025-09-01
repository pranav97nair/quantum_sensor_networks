from utils import *
from utilsIO import *
from subroutine_app import GHZProgram
import numpy as np

from squidasm.run.stack.run import run # type: ignore
from squidasm.sim.stack.common import LogManager # type: ignore

if __name__ == '__main__':
    num_nodes = 4
    ntest = 3

    # Intialize programs
    node_names = [f"Node_{i+1}" for i in range(num_nodes)]
    programs = (
        {name: GHZProgram(name, node_names) for name in node_names}
    )

    # Configure network
    network_cfg = configure_perfect_network(node_names)

    # Run simulations
    results = run(
        config=network_cfg,
        programs=programs,
        num_times=1
        )
    pprint(results)
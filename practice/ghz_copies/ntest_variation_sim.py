from utils import *
import numpy as np
import matplotlib.pyplot as plt
from squidasm.run.stack.run import run # type: ignore

if __name__ == "__main__":
    # Simulation variables
    num_nodes = 5
    num_iters = 20
    max_ntest = 10

    avg_error_rates_current = []
    avg_error_rates_current_highfid = []
    avg_error_rates_optim = []
    avg_error_rates_optim_highfid = []

    ntest_list = list(range(1, max_ntest+1))
    ntotal_list = [2*num_nodes*ntest for ntest in ntest_list]

    # Simulate network with current parameters
    for ntotal in ntotal_list:
        print(f"Simulating with current parameters: {ntotal} copies")
        # Initialize the multiple-copy programs
        programs, node_names = init_GHZ_programs(
            num_nodes=num_nodes,
            measure_qubits=True,
            full_state=False,
            num_copies=ntotal
        )

        # Load the network configuration
        #network_cfg = configure_perfect_network(node_names)
        network_cfg = configure_network(
            node_names, 
            use_high_fidelity=False, 
            use_optimistic=False)

        # Run the simulation
        results = run(
            config=network_cfg,
            programs=programs,
            num_times=num_iters,
        )

        #pprint([len(results[j][0]['measurements']) for j in range(num_nodes)])
        error_rates = []
        for k in range(num_iters):
            #print("Iteration", k)
            node_results = []
            for j in range(num_nodes):
                node_result = results[j][k]['measurements']
                node_results.append(node_result)

            node_results = np.array(node_results)
            #pprint(node_results)
            sums = node_results.sum(axis=0)
            errors = list(
                1 if (sum % num_nodes) != 0 else 0
                for sum in sums
            )
            #print(errors)
            error_rate = sum(errors)/len(errors)
            #print(error_rate)
            error_rates.append(error_rate)
        
        avg_error = np.average(error_rates)
        #print(f"Average error rate for {ntotal} copies: {avg_error}")
        avg_error_rates_current.append(avg_error)

    # Simulate network with current, high-fidelity parameters
    for ntotal in ntotal_list:
        print(f"Simulating with current, high-fidelity parameters: {ntotal} copies")
        # Initialize the multiple-copy programs
        programs, node_names = init_GHZ_programs(
            num_nodes=num_nodes,
            measure_qubits=True,
            full_state=False,
            num_copies=ntotal
        )

        # Load the network configuration
        #network_cfg = configure_perfect_network(node_names)
        network_cfg = configure_network(
            node_names, 
            use_high_fidelity=True, 
            use_optimistic=False)

        # Run the simulation
        results = run(
            config=network_cfg,
            programs=programs,
            num_times=num_iters,
        )

        #pprint([len(results[j][0]['measurements']) for j in range(num_nodes)])
        error_rates = []
        for k in range(num_iters):
            #print("Iteration", k)
            node_results = []
            for j in range(num_nodes):
                node_result = results[j][k]['measurements']
                node_results.append(node_result)

            node_results = np.array(node_results)
            #pprint(node_results)
            sums = node_results.sum(axis=0)
            errors = list(
                1 if (sum % num_nodes) != 0 else 0
                for sum in sums
            )
            #print(errors)
            error_rate = sum(errors)/len(errors)
            #print(error_rate)
            error_rates.append(error_rate)
        
        avg_error = np.average(error_rates)
        #print(f"Average error rate for {ntotal} copies: {avg_error}")
        avg_error_rates_current_highfid.append(avg_error)

    # Simulate network with optimistic parameters
    for ntotal in ntotal_list:
        print(f"Simulating with optimistic parameters: {ntotal} copies")
        # Initialize the multiple-copy programs
        programs, node_names = init_GHZ_programs(
            num_nodes=num_nodes,
            measure_qubits=True,
            full_state=False,
            num_copies=ntotal
        )

        # Load the network configuration
        #network_cfg = configure_perfect_network(node_names)
        network_cfg = configure_network(
            node_names, 
            use_high_fidelity=False, 
            use_optimistic=True)

        # Run the simulation
        results = run(
            config=network_cfg,
            programs=programs,
            num_times=num_iters,
        )

        #pprint([len(results[j][0]['measurements']) for j in range(num_nodes)])
        error_rates = []
        for k in range(num_iters):
            #print("Iteration", k)
            node_results = []
            for j in range(num_nodes):
                node_result = results[j][k]['measurements']
                node_results.append(node_result)

            node_results = np.array(node_results)
            #pprint(node_results)
            sums = node_results.sum(axis=0)
            errors = list(
                1 if (sum % num_nodes) != 0 else 0
                for sum in sums
            )
            #print(errors)
            error_rate = sum(errors)/len(errors)
            #print(error_rate)
            error_rates.append(error_rate)
        
        avg_error = np.average(error_rates)
        #print(f"Average error rate for {ntotal} copies: {avg_error}")
        avg_error_rates_optim.append(avg_error)

    # Simulate network with optimistic, high-fidelity parameters
    for ntotal in ntotal_list:
        print(f"Simulating with optimistic, high-fidelity parameters: {ntotal} copies")
        # Initialize the multiple-copy programs
        programs, node_names = init_GHZ_programs(
            num_nodes=num_nodes,
            measure_qubits=True,
            full_state=False,
            num_copies=ntotal
        )

        # Load the network configuration
        #network_cfg = configure_perfect_network(node_names)
        network_cfg = configure_network(
            node_names, 
            use_high_fidelity=True, 
            use_optimistic=True)

        # Run the simulation
        results = run(
            config=network_cfg,
            programs=programs,
            num_times=num_iters,
        )

        #pprint([len(results[j][0]['measurements']) for j in range(num_nodes)])
        error_rates = []
        for k in range(num_iters):
            #print("Iteration", k)
            node_results = []
            for j in range(num_nodes):
                node_result = results[j][k]['measurements']
                node_results.append(node_result)

            node_results = np.array(node_results)
            #pprint(node_results)
            sums = node_results.sum(axis=0)
            errors = list(
                1 if (sum % num_nodes) != 0 else 0
                for sum in sums
            )
            #print(errors)
            error_rate = sum(errors)/len(errors)
            #print(error_rate)
            error_rates.append(error_rate)
        
        avg_error = np.average(error_rates)
        #print(f"Average error rate for {ntotal} copies: {avg_error}")
        avg_error_rates_optim_highfid.append(avg_error)


    plt.plot(ntotal_list, avg_error_rates_current, c='b', label="Current")
    plt.plot(ntotal_list, avg_error_rates_current_highfid, c='r', label="Current high-fidelity")
    plt.plot(ntotal_list, avg_error_rates_optim, c='g', label="Optimistic")
    plt.plot(ntotal_list, avg_error_rates_optim_highfid, c='black', label="Optimistic high-fidelity")
    plt.xlabel("Number of copies of GHZ state")
    plt.ylabel("Average error rate")
    plt.legend(loc='lower right')
    plt.savefig("error_rate_vs_num_copies_comparison.png")
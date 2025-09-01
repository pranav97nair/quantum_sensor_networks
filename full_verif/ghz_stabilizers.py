from typing import Dict, List
from itertools import combinations
from pprint import pprint
import random

###
#   Function to output a set of stabilizer generators for the GHZ state, given the number of nodes
#   The stabilizers are output in the form of a dictionary, where the key is the stabilizer name
#   and the value is a list of Pauli observables to measure for each node
#   The function selects the first stabilizer in the generator by randomly assigning 2 nodes to measure Y.
#   The remaining nodes will measure X.
#   It then increments the indices of the nodes measuring Y by 1 n-2 times to generate 
#   the n-1 such stabilizers in the generator.
#   The nth and final stabilizer is always XX...X.
#   For example:
#       if n = 5 and nodes 2 and 3 are first measuring Y
#       we will measure the stabilizer -XYYXX
#       then we will increment both indices by 1 three times 
#       to generate -XXYYX, -XXXYY, -YXXXY
#       Then finally we will measure XXXXX
###
def get_generators(num_nodes: int) -> Dict[str, List[str]]:
    # Randomly assign 2 nodes to measure Y, all other nodes will measure X
    y_node1 = random.randint(0, num_nodes-1)
    y_node2 = (y_node1 + 1) % num_nodes

    stabilizer_bases = []
    stabilizer_names = []
    for s in range(1, num_nodes+1):    # Loop from 1 to n
        measure_bases = []
        name = ""
        if s == num_nodes:                      # Last stabilizer measured is necessarily XX...X
            for _ in range(num_nodes):
                measure_bases.append('X')
        else:
            name += "-"
            if y_node1 == 0:              # First two nodes measure Y
                measure_bases.extend(['Y', 'Y'])
                for _ in range(num_nodes-2):
                    measure_bases.append('X')
            elif y_node2 == 0:            # First and last nodes measure Y
                measure_bases.append('Y')
                for _ in range(num_nodes-2):
                    measure_bases.append('X')
                measure_bases.append('Y')
            else:                               # 2 nodes in the middle measure Y
                for _ in range(y_node1):
                    measure_bases.append('X')
                measure_bases.extend(['Y', 'Y'])
                for _ in range(num_nodes-1-y_node2):
                    measure_bases.append('X')

        stabilizer_bases.append(measure_bases)
        name += "".join(measure_bases)
        stabilizer_names.append(name)
        # Increment node indices that will measure Y
        y_node1 = y_node2
        y_node2 = (y_node2 + 1) % num_nodes

    result = {name: bases for name, bases in 
              zip(stabilizer_names, stabilizer_bases)}

    return result

###
#   Generates the full set of stabilizers of a GHZ state
#   Input : n - number of nodes in the network
#   Uses get_generators() to output a list of strings representing the generator set using X and Y Paulis
#   Uses stabilizer_product() to calculate the product of a chosen combination of stabilizers
#   Output : dictionary containing the strings representing the full set of stabilizers
###
def gen_stabilizer_set(num_nodes: int):
    # Get generator for the set of stabilizers
    stab_dict = get_generators(num_nodes)
    generators = list(stab_dict.keys())
    #print(f"Generators: \n{generators}")
 
    stab_dict['I'*num_nodes] = ['I' for i in range(num_nodes)]
    product_stabs = []
    # Get all possible 2, 3, ..., n-combinations of the stabilizers in the generator set
    for i in range(2, num_nodes+1):
        combos = combinations(generators, i)
        # For each combination, calculate the product of the chosen stabilizers
        for tup in combos:
            product_stabs.append(stabilizer_product(tup, num_nodes))
    
    for stab in product_stabs:
        bases = []
        for letter in stab[-num_nodes:]:
            bases.append(letter)
            stab_dict[stab] = bases
    
    return stab_dict


###
#   Calculates the product of multiple independent stabilizers of the GHZ state
#   Input : tuple containing the stabilizers to be multiplied and the number of nodes
#   e.g. (-XXYY, -XYYX, XXXX), 4
#   Uses pauli_product() to calculate the product for each node
#   Outputs a string representing the resulting stabilizer
###
def stabilizer_product(tup: tuple, num_nodes: int):
    # Variable to keep track of the number of -1 that appear in the product
    sign_exp = 0
    stabs = []
    for s in tup:
        if s[0] == '-':
            sign_exp += 1
        stabs.append(s[-num_nodes:])

    result = ''
    # For each node
    for i in range(num_nodes):
        # Calculate the pauli product
        paulis = [s[i] for s in stabs]
        prod, sign_count = pauli_product(paulis)
        # Account for the sign of the product
        sign_exp = (sign_exp + sign_count) % 2
        # Decode the product to output strings
        if prod == 0:
            result += 'I'
        elif prod == 1:
            result += 'X'
        elif prod == 2:
            result += 'Y'
        else:
            result += 'Z'
    
    # Calculate the sign
    sign = (-1)**sign_exp
    if sign < 0:
        result = '-' + result

    return result

###
#   Calculates the product of single qubit Paulis from a given list
#   Note - Since our generator set only consists of X and Y, this function is only defined to account for
#   an input list containing X and Y
#   Outputs an integer representing I, X, Y or Z 
#   and a count of the -1 that appeared during the multiplication
###
def pauli_product(paulis: List[str]):
    paulis_int = []
    # Variable to keep track of all the -1
    sign_count = 0
    # Variable to keep track of all the i that appear
    i_count = 0
    # Convert the input string list into an integer list
    for pauli in paulis:
        if pauli == 'X':
            paulis_int.append(1) # Encoding for X
        if pauli == 'Y':
            paulis_int.append(2) # Encoding for Y
    # Encoding for Z will be 3 and I will 0
    
    # Variable to track current product as we loop through the Paulis in the input list
    result = 0

    # Loop through the Paulis and calculate the possible products
    for i in paulis_int:
        if i == result:     # XX, YY, ZZ = I
            result = 0
        elif result == 0:   # IS = S for all S
            result = i  
        elif (result - i) == 2:   # ZX = iY
            i_count += 1
            result = 2
        else:   # XY = iZ, YX = -iZ, ZY = -iX (XZ or YZ would never occur since no Z in input)
            if i < result: # YX or ZY
                sign_count += 1
            i_count += 1
            result = (result + i) % 4
    
    # We pick up a -1 for every 2 i
    sign_count += (i_count / 2)

    return result, sign_count

if __name__ == '__main__':
    num_nodes = 5
    stabilizers = gen_stabilizer_set(num_nodes)
    pprint(stabilizers)

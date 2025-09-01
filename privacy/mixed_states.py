#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jul 12 18:03:36 2023

@author: santiago
"""

import numpy as np
import pandas as pd
import itertools
import matplotlib.pyplot as plt
import os

import aux
import plot_functions as pf
import kraus_operators as ko
import save_results as sr
import animation

# import plt_parameters


#%%


def bell_pairs_state(d):
    if d % 2 != 0 or d < 2:
        raise ValueError("Dimension d must be an even integer greater than or equal to 2.")
    
    # Bell pair: (|00> + |11>)/sqrt(2)
    bell_pair = np.array([1, 0, 0, 1]) / np.sqrt(2)
    
    # Start with a single bell pair
    state = bell_pair
    
    # Tensor product (Kronecker) for d/2 Bell pairs
    for _ in range(d // 2 - 1):
        state = np.kron(state, bell_pair)
    
    return state


#%%
def density_matrix(state, d, alpha=0, dicke_n_ones=0):
    
    if state=='GHZplus':
        rho_GHZ = density_matrix('GHZ', d)
        rho_plus = density_matrix('plus', d)
        rho_GHZplus = (1-alpha) * rho_GHZ + alpha * rho_plus
        return rho_GHZplus
        
    elif state=='GHZ':
        coefficients = np.zeros(2**d)
        coefficients[0] = coefficients[-1] = 1
        coefficients = coefficients/np.linalg.norm(coefficients)
    
    elif state=='Bell': # Phi+
        coefficients = bell_pairs_state(d)
        coefficients = coefficients/np.linalg.norm(coefficients)
    
    elif state=='plus':
        # |+++>
        coefficients = np.ones(2**d)
        coefficients = coefficients/np.linalg.norm(coefficients)
    
    elif state=='minus':
        # |--->
        coefficients = np.ones(2**d)
        for i in range(2**d):
            coefficients[i] = (-1)**(i.bit_count())
        coefficients = coefficients/np.linalg.norm(coefficients)
        
    elif state=='plus_and_minus':
        coefficients_plus = np.ones(2**d)
        coefficients_minus = np.ones(2**d)        
        for i in range(2**d):
            coefficients_minus[i] = (-1)**(i.bit_count())
        coefficients = coefficients_plus + coefficients_minus
        coefficients = coefficients/np.linalg.norm(coefficients)
    
    elif state=='W':
        coefficients = np.zeros(2**d)
        for n in range(d):
            coefficients[2**n] = 1
        coefficients = coefficients/np.linalg.norm(coefficients)
    
    elif state=='random_noise':
        coefficients = 2*np.random.rand(2**d)-1 + 2*np.random.rand(2**d)*1j-1j
        coefficients[0] = coefficients[-1] = 0
        coefficients = coefficients/np.linalg.norm(coefficients)
    
    elif state=='Dicke':
        coefficients = np.zeros(2**d)
        for i in range(len(coefficients)):
            if i.bit_count() == dicke_n_ones:
                coefficients[i] = 1
        coefficients = coefficients/np.linalg.norm(coefficients)
        
    elif state=='bundle_4_2':
            # bundled graph state with d=4 parameters and n=2 nodes.
            coefficients = np.ones(2**4)
            coefficients[5] = coefficients[6] = coefficients[9] = coefficients[10] = -1
            coefficients = coefficients/np.linalg.norm(coefficients)
    
    elif state=='bundle_6_2':
            # bundled graph state with d=6 parameters and n=2 nodes.
            coefficients = np.ones(2**6)
            coefficients[3] = coefficients[6] = coefficients[9] = coefficients[12] = coefficients[18] = coefficients[23] = coefficients[24] = coefficients[29] = coefficients[33] = coefficients[36] = coefficients[43] = coefficients[46] = coefficients[48] = coefficients[53] = coefficients[58] = coefficients[63] = -1
            coefficients = coefficients/np.linalg.norm(coefficients)
    elif state=='bundle_6_3':
            # bundled graph state with d=6 parameters and n=2 nodes.
            coefficients = np.ones(2**6)
            coefficients[5] = coefficients[6] = coefficients[9] = coefficients[10] = coefficients[17] = coefficients[18] = coefficients[20] = coefficients[21] = coefficients[22] = coefficients[23] = coefficients[24] = coefficients[25] = coefficients[26] = coefficients[27] = coefficients[29] = coefficients[30] = coefficients[33] = coefficients[34] = coefficients[36] = coefficients[37] = coefficients[38] = coefficients[39] = coefficients[40] = coefficients[41] = coefficients[42] = coefficients[43] = coefficients[45] = coefficients[46] = coefficients[53] = coefficients[54] = coefficients[57] = coefficients[58] = -1
            coefficients = coefficients/np.linalg.norm(coefficients)
                
    # if flags['print_states']:
    #     print_state(state,d, coefficients)
    
    rho = np.tensordot(np.conj(coefficients), coefficients, axes=0)
    return rho



def print_state(state, d, coefficients):
    
    basis = list(itertools.product([0, 1], repeat=d))
    psi = ''
    for c,b in zip(coefficients, basis):
        if c:
            psi = psi + ' + ' + '%.3f'%c + '\t| %s >'%str(b).strip('()') + '\n'
    
    print(state + ':')
    print(psi)



#%%

def H_and_M(d, operator='sigma_z', print_matrices:bool=False):
    
    sigma_x = np.array([[0, 1],[1, 0]])
    # sigma_y = np.array([[0, -1j],[1j, 0]])
    sigma_z = np.diag([1, -1])
    id_2 = np.diag([1, 1])
    
    if operator=='sigma_z':
        OP = sigma_z/2
    elif operator=='hadamard':
        OP = sigma_z/2 + sigma_x/2
    elif operator=='sigma_x':
         OP = sigma_x/2
    else:
        print('Operator not yet implemented in function "H_and_M".')
        from sys import exit
        exit()
    
    # Operators:
    H = {}
    for i in range(d):
        H[i] = np.ones((1,1))
        for j in range(d):
            if i==j:
                H[i] = np.kron(H[i], OP)
            else:
                H[i] = np.kron(H[i], id_2)
    
    
    M = {}
    
    for i in range(d-1):
        M[i] = {}
    
    for i in range(d):
        for j in range(i, d):
            if j!=i:
                M[i][j] = H[i] - H[j]

            # Printing:
            if print_matrices:
                print('M[%d][%d] =\n'%(i,j), M[i][j], '\n')
    
    return H, M


def trace_norm(m):
    '''
    Parameters
    ----------
    M : Numpy 2d-array

    Returns
    -------
    The "trace norm" of M.

    '''
    
    '''
    # Examples:
    m = np.matrix('1 2 3; 1 1 1; 2 2 2')
    m = np.matrix('1 0 0; 0 1 0; 0 0 1')
    m = np.matrix('0.5 0 0 0.5; 0 0 0 0; 0 0 0 0; 0.5 0 0 0.5')

    m = np.matrix('0.5 0; 0 -0.5')
    m = np.matrix('-1 0 0; 0 -2 0; 0 0 3')
    '''
    s = sum(np.linalg.svd(m)[1])
    return s

def apply_noise(rho, d:int, K:list):
    '''
    Parameters
    ----------
    rho : Numpy 2d-array
        Density matrix of the state to apply .
    d : int
        dimension.
    K : list
        List of Kraus operators.

    Returns
    -------
    s : Numpy 2d-array
        Density matrix after noise.
    '''
    s = np.zeros((2**d, 2**d))
    for i in range(len(K)):
        s = s + np.matmul(np.matmul(K[i], rho), np.conjugate(np.transpose(K[i])))
    s = s
    return s


#%%


def mixed_states(d:int, state:str, eta_values:list, alpha_values:list, plots_path:str, colours:dict, colourbar_limits:dict, flags:dict, noise_types:list, pause_between_plots:float=0.0, H_operator='sigma_z', dicke_n_ones=0):
    
    H, M = H_and_M(d, operator=H_operator, print_matrices=False)
    
    if flags['plot_H_and_M']:
        for i in range(len(H)):
            pf.plot_matrix(H[i],
                           plot='3d',
                           save = flags['save_H_and_M'],
                           save_name = 'H_%d'%(i),
                           path = plots_path + 'H',
                           colour = colours['H'],
                           clim = colourbar_limits['H'],
                           save_as = 'png'
                           )
    
        for i in M.keys():
            for j in M[i].keys():
                pf.plot_matrix(M[i][j],
                            save = flags['save_H_and_M'],
                            save_name = 'M_%d_%d'%(i,j),
                            path = plots_path + 'M',
                            colour = colours['M'],
                            clim = colourbar_limits['M'],
                            save_as = 'png'
                            )
    
    data = {}
    
    data['parameters'] = pd.DataFrame()
    
    data['parameters']['parameter'] = parameters.keys()
    data['parameters']['value'] = parameters.values()
    
    # noise_types = ['Dephasing Noise'] #['Depolarising Noise', 'Amplitude Damping', 'Phase Damping']#, 'Dephasing Noise']
    
    for noise in noise_types:
        data[noise] = pd.DataFrame(columns = ['alpha', 'eta', 'epsilon'])
    
    
    for alpha in alpha_values:
        for eta in eta_values:
            print('\ralpha:\t%.2f\t\teta:\t%.2f'%(alpha, eta), end='')
            Kraus_operators = {'Amplitude Damping': ko.amplitude_damping_Kraus_operators(d, eta),
                               'Depolarising Noise': ko.depolarising_Kraus_operators(d, eta),
                               'Phase Damping': ko.phase_damping_Kraus_operators(d, eta),
                               'Dephasing Noise': ko.dephasing_Kraus_operators(d, eta),
                               }
            
            for noise in noise_types:
                
                path = plots_path + noise + os.sep
                
                K = Kraus_operators[noise]
                
                # rho_GHZ = density_matrix('GHZ', d)
                # rho_plus = density_matrix('plus', d)
                # rho_0 = (1-alpha) * rho_GHZ + alpha * rho_plus
                
                rho_0 = density_matrix(state, d, alpha, dicke_n_ones=dicke_n_ones)
                
                rho_with_noise = apply_noise(rho_0, d, K)
                
                if flags['save_rho_csv']:
                    aux.check_dir(plots_path)
                    sr.save_matrix(m = rho_with_noise,
                                   d = d,
                                   eta = eta,
                                   alpha = alpha,
                                   filename = 'rho_eta=%.2f_alpha=%.2f'%(eta, alpha),
                                   path = path + 'rho_txt',
                                   noise = noise)
                
                
                if flags['plot_rho']:
                    pf.plot_matrix(np.real(rho_with_noise),
                                   plot = '3d',
                                   title = r'%s \quad %s \quad $Re(\rho) \quad \alpha=%.2f \quad \eta=%.2f$'%(state, noise, alpha,eta),
                                   save = flags['save_rho'],
                                   save_name='%s_rho_eta=%.2f_alpha=%.2f_re'%(state, eta, alpha),
                                   path = path + 'rho',
                                   colour=colours['rho_re'],
                                   clim=colourbar_limits['rho_re'],
                                   save_as = 'pdf'
                                   )
                    pf.plot_matrix(np.imag(rho_with_noise),
                                   plot='3d',
                                   title=r'%s \quad %s \quad $Im(\rho) \quad \alpha=%.2f \quad \eta=%.2f$'%(state, noise, alpha,eta),
                                   save=flags['save_rho'],
                                   save_name='%s_rho_eta=%.2f_alpha=%.2f_im'%(state, eta, alpha),
                                   path = path + 'rho',
                                   colour=colours['rho_im'],
                                   clim=colourbar_limits['rho_im'],
                                   save_as = 'pdf'
                                   )
                    plt.pause(pause_between_plots)
        
                C = {}
                for i in range(d-1):
                    C[i] = {}
                
                # norms = []
                trace_norms = []
                for i in M.keys():
                    for j in M[i].keys():
                        C[i][j] = np.matmul(M[i][j], rho_with_noise) - np.matmul(rho_with_noise, M[i][j])
                        # norms.append(np.linalg.norm(C[i][j], 1))
                        trace_norms.append(trace_norm(C[i][j]))
                
                print('\ntrace norms:', trace_norms)
                # epsilon = max(norms)
                # epsilon = max(trace_norms)
                epsilon = round(sum(trace_norms)/(np.sqrt(2)*len(trace_norms)), 6)
                print('\nepsilon(%s):'%state, epsilon)
                
                l = len(data[noise])
                data[noise].at[l, 'alpha'] = alpha
                data[noise].at[l, 'eta'] = eta
                data[noise].at[l, 'epsilon'] = epsilon
                
                
                if flags['plot_C']:
                    for i in C.keys():
                        for j in C[i].keys():
                            pf.plot_matrix(np.real(C[i][j]),
                                           title='$\eta=%.2f$ - $Re$'%eta,
                                           save=flags['save_C'],
                                              save_name='%s_C_%d_%d_eta=%.2f_alpha=%.2f_re'%(state, i, j, eta, alpha),
                                              path = path + 'C',
                                              colour = colours['C'],
                                              clim = colourbar_limits['C'],
                                              save_as = 'png'
                                              )
                            pf.plot_matrix(np.imag(C[i][j]),
                                           title='$\eta=%.2f$ - $Im$'%eta,
                                           save=flags['save_C'],
                                           save_name='%s_C_%d_%d_eta=%.2f_alpha=%.2f_im'%(state, i,j, eta, alpha),
                                           path = path + 'C',
                                           colour=colours['C'],
                                           clim=colourbar_limits['C'],
                                           save_as = 'png'
                                           )
            plt.close('all')
    
    if flags['save_results']:
        sr.save_results(data=data, filename = plots_path + 'data_' + state + '_d=' + str(d))
                    
    if flags['plot_epsilon']:
        for noise in noise_types:
            pf.plot_epsilon(d,
                            data,
                            noise,
                            plot = '2d',
                            title = '',
                            save = flags['save_epsilon'],
                            save_name = 'data',
                            path = plots_path,
                            state = state
                            )





if __name__=='__main__':
    
    # parameters = aux.read_parameters('parameters.txt')

    # Parameters
    parameters = {}
    
    H_operator = 'sigma_z'
    parameters['label'] = 'H=%s'%H_operator
    
    parameters['date'] = aux.get_date()
    
    parameters['d'] = 4
    
    parameters['state'] = 'plus'
    states = ['GHZ', 'plus', 'minus', 'plus_and_minus', 'GHZplus', 'W', 'Dicke', 'bundle_4_2', 'bundle_6_2']
    
    parameters['eta_min'] = 0
    parameters['eta_max'] = 1
    parameters['n_eta'] = 1
    parameters['eta_values'] = np.linspace(parameters['eta_min'],
                                           parameters['eta_max'],
                                           num=parameters['n_eta'],
                                           )
    
    parameters['alpha_min'] = 0
    parameters['alpha_max'] = 1
    parameters['n_alpha'] = 1
    parameters['alpha_values'] = np.linspace(parameters['alpha_min'],
                                             parameters['alpha_max'],
                                             num=parameters['n_alpha'],
                                             )
    
    parameters['noise_types'] = ['Amplitude Damping', 'Depolarising Noise', 'Dephasing Noise', 'Phase Damping']
    
    plots_path = aux.make_path(['plots', parameters['label'], parameters['state'],'d=%d'%parameters['d']])
    
    parameters['colours'] = {'H': 'coolwarm',
               'M': 'PiYG',
               'rho_re': 'inferno_r',
               'rho_im': 'cividis',
               'C': 'viridis'}
    
    parameters['colourbar_limits'] = {'H': [-1, 1],
                                      'M': [-1, 1],
                                      'rho_re': [-0.55, 0.55],
                                      'rho_im': [-0.55, 0.55],
                                      'C': [-0.55, 0.55]}
    # Flags
    
    flags = {'verify_parameters': 1,
             'save_parameters': 0,
             
             'print_states': 0,
             
             'plot_H_and_M': 1,
             'save_H_and_M': 1,
             
             'plot_rho': 0,
             'save_rho': 1,
             'save_rho_csv': 0, # rho in TXT
             
             'plot_C': 1,
             'save_C': 1,
             
             'plot_epsilon': 1,
             'save_epsilon': 1,
             
             'save_results': 0, # xlsx
             
             'animations': 0,
             }
    
    if flags['verify_parameters']:
        aux.verify_parameters(parameters)
    
    
    if parameters['state'] == 'Dicke':
        dicke_n_ones = list(range(parameters['d']))
    else:
        dicke_n_ones = [0]
    
    for n_ones in dicke_n_ones:
        if parameters['state'] == 'Dicke':
            mixed_states(d = parameters['d'],
                         state = parameters['state'],
                         eta_values = parameters['eta_values'],
                         alpha_values = parameters['alpha_values'],
                         plots_path = plots_path + 'n_ones=%d/'%n_ones,
                         colours = parameters['colours'],
                         colourbar_limits = parameters['colourbar_limits'],
                         flags = flags,
                         noise_types = parameters['noise_types'],
                         pause_between_plots = 0,
                         H_operator = H_operator,
                         dicke_n_ones = n_ones
                         )
        else:
            mixed_states(d = parameters['d'],
                         state = parameters['state'],
                         eta_values = parameters['eta_values'],
                         alpha_values = parameters['alpha_values'],
                         plots_path = plots_path,
                         colours = parameters['colours'],
                         colourbar_limits = parameters['colourbar_limits'],
                         flags = flags,
                         noise_types = parameters['noise_types'],
                         pause_between_plots = 0,
                         H_operator = H_operator,
                         dicke_n_ones = n_ones
                         )
    

    variables_animations = ['rho']#, 'C_0_1']

    if flags['animations']:
        for var in variables_animations:
            print('\n%s:'%var)
            for alpha in parameters['alpha_values']:
                print('alpha=', alpha)
                animation.animate(label = parameters['label'],
                                  state = parameters['state'],
                                  d = parameters['d'],
                                  var = var,
                                  noise_types = parameters['noise_types'],
                                  FPS = 16,
                                  initial_seconds = 2,
                                  final_seconds = 2,
                                  alpha = alpha,
                                  )
import copy
import subprocess
import random
import matplotlib.pyplot as plt
import re
import time
from fsm_class import *
from tfsm_class import *
from ansible import *
from saltstack import *

from datetime import datetime

def experimental_evaluation(tfsm, length, number):
    delta_sum = 0.0
    time_execution_simple_sum = 0.0
    time_execution_optimal_sum = 0.0
    fsm_inputs = list(tfsm.base_fsm.fsm_inputs)
    random_traces = [[random.choice(fsm_inputs) for _ in range(length)] for _ in range(number)]
    for trace in random_traces:
        naive_safe_trace = tfsm.derive_naive_safe_trace(trace)
        cmt_safe_trace = tfsm.derive_a_safe_trace(trace)
        time_execution_simple = tfsm.derive_response_time(naive_safe_trace)
        time_execution_optimal = tfsm.derive_response_time(cmt_safe_trace)
        delta = time_execution_simple / time_execution_optimal
        delta_sum += delta
        time_execution_simple_sum += time_execution_simple
        time_execution_optimal_sum += time_execution_optimal
    delta_average = float(delta_sum / number)
    time_execution_simple_average = float(time_execution_simple_sum / number)
    time_execution_optimal_average = float(time_execution_optimal_sum / number)
    return (delta_average, time_execution_simple_average, time_execution_optimal_average)

def build_graph(tfsm, x_array, y_array, z_array, d_array):
    average_delta = dict()
    time_execution_simple_dict = dict()
    time_execution_optimal_dict = dict()
    #for length in range(10, 200, 10):
    for length in range(10, 500, 10):
        (average_delta[length], time_execution_simple_dict[length], time_execution_optimal_dict[length]) = experimental_evaluation(tfsm, length, 100)
        x_array.append(length)
        y_array.append(time_execution_simple_dict[length])
        z_array.append(time_execution_optimal_dict[length])
        d_array.append(average_delta[length])
    print("average_delta =", average_delta)
    return

def build_graph_from_file(tfsm, file_name):
    file = open(file_name, 'w')
    x_array = file.readline()
    y_array = file.readline()
    x_array_list = x_array.split(' ')
    y_array_list = y_array.split(' ')
    plt.plot(x_array_list, y_array_list, color='blue')
    plt.show()
    return

def experiments():
    input_file = "tests/input1.txt"
    output_file = "tests/output1.fsm"
    fsm = FSM(input_file)
    fsm.parse_inputs_outputs_states()
    fsm.derive_fsm_bfs()
    fsm.derive_reversed_fsm()
    tfsm = TFSM(fsm)
    tfsm.refine_tfsm("tests/minimax_ansible.txt", "tests/tfsm_ansible.tfsm")
    ##########
    x_array = list()
    ansible_array = list()
    ansible_array_opt = list()
    build_graph(tfsm, x_array, ansible_array, ansible_array_opt)

    plt.plot(x_array, ansible_array, 'b', label='without CMTVeriSafe')
    plt.plot(x_array, ansible_array_opt, 'b--', label='with CMTVeriSafe')
    plt.xlabel("Number of commands in a tenant request")
    plt.ylabel("Average execution time (sec)")
    plt.legend()
    plt.show()

    return

def experiment_ansible():
    input_file = "tests/input1.txt"
    fsm = FSM(input_file)
    fsm.parse_inputs_outputs_states()
    fsm.derive_fsm_bfs()
    fsm.derive_reversed_fsm()
    tfsm = TFSM(fsm)
    tfsm.refine_tfsm("tests/minimax_ansible.txt", "tests/tfsm_ansible.tfsm")
    ##########
    x_array = list()
    ansible_array = list()
    ansible_array_opt = list()
    delta_array = list()
    build_graph(tfsm, x_array, ansible_array, ansible_array_opt, delta_array)
    plt.figure()
    line, = plt.plot(x_array, ansible_array, 'b', label='without CMTVeriSafe')
    line.set_color('black')
    line, = plt.plot(x_array, ansible_array_opt, 'b--', label='with CMTVeriSafe')
    line.set_color('black')
    plt.xlabel("Number of commands in a tenant request")
    plt.ylabel("Average execution time (sec)")
    plt.legend()
    plt.savefig("ansible_result_u.png")
    return (x_array, delta_array)

def experiment_salt():
    input_file = "tests/input1.txt"
    fsm = FSM(input_file)
    fsm.parse_inputs_outputs_states()
    fsm.derive_fsm_bfs()
    fsm.derive_reversed_fsm()
    tfsm = TFSM(fsm)
    tfsm.refine_tfsm("tests/minimax_salt.txt", "tests/tfsm_salt.tfsm")
    ##########
    x_array = list()
    salt_array = list()
    salt_array_opt = list()
    delta_array = list()
    build_graph(tfsm, x_array, salt_array, salt_array_opt, delta_array)
    plt.figure()
    line, = plt.plot(x_array, salt_array, 'b', label='without CMTVeriSafe')
    line.set_color('black')
    line, = plt.plot(x_array, salt_array_opt, 'b--', label='with CMTVeriSafe')
    line.set_color('black')
    plt.xlabel("Number of commands in a tenant request")
    plt.ylabel("Average execution time (ms)")
    plt.legend()
    plt.savefig("salt_result_u.png")
    return (x_array, delta_array)

def derive_delta_graph(x_array, delta_ansible, delta_salt):
    plt.figure()
    line, = plt.plot(x_array, delta_ansible, 'b', label='ansible')
    line.set_color('black')
    line, = plt.plot(x_array, delta_salt, 'b--', label='salt')
    line.set_color('black')
    plt.xlabel("Number of commands in a tenant request")
    plt.ylabel("Response_time(naive) / Response_time(CMT-VSE)")
    plt.legend()
    plt.savefig("delta_result_u.png")
    return

def demo():
    input_file = "tests/input1.txt"
    output_file = "tests/output1.fsm"
    fsm = FSM(input_file)
    fsm.parse_inputs_outputs_states()
    fsm.derive_fsm_bfs()
    fsm.print_in_fsm_format(output_file)
    fsm.derive_reversed_fsm()

    # output_sls_file = open("tests/salt_state1.sls", 'w')
    salt = SaltStack(fsm.fsm_inputs)
    # trace = ["vm2_close", "vm2_deny_sub1", "vm2_open", "vm2_allow_sub1", "vm1_send_vm2", "vm2_close", "vm2_deny_sub1"]
    # salt_trace = salt.dervie_salt_state_for_a_trace(trace, 2)
    # output_sls_file.write(salt_trace)

    tfsm = TFSM(fsm)
    # tfsm.derive_TFSM_for_salt(False)
    # tfsm.print_in_tfsm_format()

    tfsm.refine_tfsm("tests/minimax_ansible.txt", "tests/tfsm_ansible.tfsm")
    # tfsm.print_in_tfsm_format()

    trace = ["vm2_close", "vm2_deny_sub1", "vm2_open", "vm2_allow_sub1", "vm1_send_vm2", "vm2_close", "vm2_deny_sub1"]
    safe_trace = tfsm.derive_a_safe_trace(trace)
    print("safe_trace =", safe_trace)
    print("response_time =", tfsm.derive_response_time(safe_trace))
    safe_naive_trace = tfsm.derive_naive_safe_trace(trace)
    print("safe_naive_trace =", safe_naive_trace)
    print("response_time_naive =", tfsm.derive_response_time(safe_naive_trace))

    content = salt.dervie_salt_state_for_a_timed_trace(safe_trace, 1)
    output_sls_file = open("tests/salt_state_safe_trace.sls", 'w')
    output_sls_file.write(content)

(x_array, delta_ansible) = experiment_ansible()
(x2_array, delta_salt) = experiment_salt()
derive_delta_graph(x_array, delta_ansible, delta_salt)
#demo()
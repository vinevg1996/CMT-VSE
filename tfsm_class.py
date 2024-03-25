import copy
import re
import time
import subprocess
from fsm_class import *
from ansible import *
from saltstack import *
from datetime import datetime

class TimedTransition:
    def __init__(self, start_state, i, u, v, o, d, end_state):
        self.start_state = copy.deepcopy(start_state)
        self.i = str(i)
        self.u = str(u)
        self.v = str(v)
        self.o = str(o)
        self.d = str(d)
        self.end_state = copy.deepcopy(end_state)
        #self.timed_tran = [self.start_state.derive_vector(), self.i, self.u, self.v, self.end_state.derive_vector(), self.o, self.d]
        return

    def print(self):
        # print(self.tran)
        s_start_vec = self.start_state.derive_vector()
        #s_start = int(s_start_vec, 2)
        s_end_vec = self.end_state.derive_vector()
        #s_end = int(s_end_vec, 2)
        out_line = str(s_start_vec) + ' ' + str(self.i) + ' ' + str(self.u) + ' ' + str(self.v) + ' ' + str(self.o) +  ' ' + str(self.d) + ' ' + str(s_end_vec)
        print(out_line)
        return

class TFSM:
    def __init__(self, fsm):
        self.base_fsm = copy.deepcopy(fsm)
        self.u_fluctuation = dict()
        self.v_fluctuation = dict()
        self.delays = dict()
        return

    def refine_tfsm(self, minimax_file_name, tfsm_file_name):
        tfsm_file = open(tfsm_file_name, 'r')
        self.min_p = dict()
        self.max_q = dict()
        minimax_file = open(minimax_file_name, 'r')
        j = 0
        for line in minimax_file:
            line_list = line.split('\n')[0].split(':')
            if j % 2 == 0:
                self.min_p[line_list[0]] = float(line_list[1])
            else:
                self.max_q[line_list[0]] = float(line_list[1])
            j += 1
        for line in tfsm_file:
            line_list = line.split('\n')[0].split(' ')
            state = line_list[0]
            i = line_list[1]
            i_value = self.base_fsm.fsm_inputs[int(line_list[1])]
            tran = self.base_fsm.states[state][i_value]
            u = float(line_list[2])
            v = float(line_list[3])
            o = line_list[4]
            d = float(line_list[5])
            timed_tran = TimedTransition(tran.start_state, i, u, v, o, d, tran.end_state)
            timed_tran.print()
            self.base_fsm.states[state][i_value] = timed_tran
        for state in self.base_fsm.states.keys():
            for curr_input in self.base_fsm.states[state].keys():
                timed_tran = self.base_fsm.states[state][curr_input]
                u = float(timed_tran.u)
                v = float(timed_tran.v)
                d = float(timed_tran.d)
                if ("open" in curr_input) or ("allow" in curr_input):
                    for contr_input in self.base_fsm.contr_state_bits.keys():
                        if self.base_fsm.contr_state_bits[contr_input] == curr_input:
                            #v_phi = max(v, self.max_q[contr_input] - d)
                            v_phi = max(v, self.max_q[contr_input] - self.min_p[curr_input])
                            print("v_phi =", v_phi)
                            timed_tran.v = float(v_phi)
                if "send" in curr_input:
                    up = 0.0
                    for i in self.base_fsm.state_bits:
                        if self.max_q[i] - d > up:
                            up = float(self.max_q[i]) - d
                    v_phi = max(up, v)
                    timed_tran.v = float(v_phi)
        return

    def calculate_efficiency_coefficient(self, trace):
        #time_salt = list()
        state = self.base_fsm.initial_state
        time_salt = 0.0
        for curr_input in trace:
            u = float(self.base_fsm.states[state.derive_vector()][curr_input].u)
            # time_salt = time_salt + self.max_q[curr_input]
            time_salt = time_salt + (u + self.max_q[curr_input])
            state = self.base_fsm.states[state.derive_vector()][curr_input].end_state
        start_time = time.time()
        timestamp = 0.0
        time_opt_salt = list()
        state = self.base_fsm.initial_state
        j = 0
        for curr_input in trace:
            u = float(self.base_fsm.states[state.derive_vector()][curr_input].u)
            v = float(self.base_fsm.states[state.derive_vector()][curr_input].v)
            d = float(self.base_fsm.states[state.derive_vector()][curr_input].d)
            if ("open" in curr_input) or ("allow" in curr_input):
                for contr_input in self.base_fsm.contr_state_bits.keys():
                    if self.base_fsm.contr_state_bits[contr_input] == curr_input:
                        contr_input_places = [index for index, value in enumerate(trace[0:j]) if value == contr_input]
                        is_v = False
                        for index in contr_input_places:
                            if time_opt_salt[index] >= timestamp + d:
                                is_v = True
                        if is_v:
                            timestamp += v
                        else:
                            timestamp += u
            state = self.base_fsm.states[state.derive_vector()][curr_input].end_state
            time_opt_salt.append(timestamp + d)
            j += 1
        time_opt_salt_value = max(time_opt_salt)
        end_time = time.time()
        execution_time = end_time - start_time
        delta = float(time_salt) / float(time_opt_salt_value)
        return (delta, execution_time, time_salt, time_opt_salt_value)

    def derive_response_time(self, timed_trace):
        state = self.base_fsm.initial_state
        response_time = 0.0
        for (curr_input, timestamp) in timed_trace:
            d = float(self.base_fsm.states[state.derive_vector()][curr_input].d)
            if timestamp + d > response_time:
                response_time = float(timestamp + d)
            state = self.base_fsm.states[state.derive_vector()][curr_input].end_state
        return response_time

    def derive_naive_safe_trace(self, trace):
        safe_trace = []
        state = self.base_fsm.initial_state
        if len(trace) > 0:
            timestamp = float(self.base_fsm.states[state.derive_vector()][trace[0]].u)
            safe_trace.append((trace[0], timestamp))
            for j in range(1, len(trace)):
                d_pred = float(self.max_q[trace[j-1]])
                u = float(self.base_fsm.states[state.derive_vector()][trace[j]].u)
                v = float(self.base_fsm.states[state.derive_vector()][trace[j]].v)
                timestamp = timestamp + (u + d_pred)
                #timestamp = timestamp + (v + d_pred)
                safe_trace.append((str(trace[j]), float(timestamp)))
                j += 1
            return safe_trace
        else:
            return None

    def derive_a_safe_trace(self, trace):
        state = self.base_fsm.initial_state
        out_fsm_trace = list()
        for curr_input in trace:
            o = str(self.base_fsm.states[state.derive_vector()][curr_input].o)
            out_fsm_trace.append(o)
            state = self.base_fsm.states[state.derive_vector()][curr_input].end_state
        safe_trace = []
        timestamp = 0.0
        response_time_list = list()
        state = self.base_fsm.initial_state
        j = 0
        for curr_input in trace:
            u = float(self.base_fsm.states[state.derive_vector()][curr_input].u)
            v = float(self.base_fsm.states[state.derive_vector()][curr_input].v)
            d = float(self.base_fsm.states[state.derive_vector()][curr_input].d)
            if curr_input in self.base_fsm.state_bits:
                if '1' in out_fsm_trace:
                    max_response_time = 0.0
                    for l in range(0,j):
                        if (self.base_fsm.state_bits_contr_bits[curr_input] == trace[l]) and (response_time_list[l] > max_response_time):
                            max_response_time = float(response_time_list[l])
                    if max_response_time > timestamp + u + d:
                        timestamp = max_response_time - d
                    else:
                        timestamp = timestamp + u
                else:
                    timestamp = timestamp + u
            elif curr_input in self.base_fsm.contr_state_bits:
                timestamp = timestamp + u
            else:
                if out_fsm_trace[j] == '1':
                    max_response_time = 0.0
                    for l in range(0, j):
                        if (trace[l] in self.base_fsm.state_bits) and (response_time_list[l] > max_response_time):
                            max_response_time = float(response_time_list[l])
                    if max_response_time > timestamp + u + d:
                        timestamp = max_response_time - d
                    else:
                        timestamp = timestamp + u
                else:
                    timestamp = timestamp + u
            safe_trace.append((curr_input, timestamp))
            state = self.base_fsm.states[state.derive_vector()][curr_input].end_state
            response_time_list.append(timestamp + d)
            j += 1
        return safe_trace

    def derive_salt_files_for_transitions(self):
        N = 2
        j = 0
        for state in self.base_fsm.states.keys():
            for input in self.base_fsm.states[state].keys():
                #tran = self.base_fsm.states[state.derive_vector()][input]
                trace = list(self.base_fsm.cover_set[state])
                trace += [input]
                #print("trace = ", trace)
                salt = SaltStack(self.base_fsm.fsm_inputs)
                salt_file_content = salt.dervie_salt_state_for_a_trace(trace, N)
                curr_salt_file_name = "salt_files/out_test_" + str(j) + ".sls"
                curr_salt_file = open(curr_salt_file_name, 'w')
                curr_salt_file.write(salt_file_content)
                j += 1
        return

    def derive_salt_file_for_transition(self, state, input, index, N):
        trace = list(self.base_fsm.cover_set[state])
        trace += [input]
        print("trace = ", trace)
        salt = SaltStack(self.base_fsm.fsm_inputs)
        salt_file_content = salt.dervie_salt_state_for_a_trace(trace, N)
        curr_salt_file_name = "/srv/salt/salt_files/out_test_" + str(index) + ".sls"
        curr_salt_file = open(curr_salt_file_name, 'w')
        curr_salt_file.write(salt_file_content)
        return curr_salt_file_name

    def derive_ansible_file_for_transition(self, state, input, index, N):
        trace = list(self.base_fsm.cover_set[state])
        trace += [input]
        #trace = ["vm2_close", "vm2_deny_sub1", "vm2_open", "vm2_allow_sub1", "vm1_send_vm2"]
        print("trace = ", trace)
        curr_ansible_file_name = "out_test_" + str(index) + ".yaml"
        ansible = Ansible_playbook(curr_ansible_file_name, N)
        for i in range(0, N):
            for in_command in trace:
                ansible.add_task(in_command, i)
        ansible.collect_playbook()
        return curr_ansible_file_name

    def derive_TFSM_for_salt(self, is_salt):
        N = 3
        j = 0
        self.u_dict = dict()
        self.v_dict = dict()
        self.p_dict = dict()
        self.q_dict = dict()
        min_delays = dict()
        max_delays = dict()
        self.min_p = dict()
        self.max_q = dict()
        for i in self.base_fsm.fsm_inputs:
            min_delays[i] = list()
            max_delays[i] = list()
            self.min_p[i] = 0.0
            self.max_q[i] = 0.0
        for state in self.base_fsm.states.keys():
            self.u_dict[state] = dict()
            self.v_dict[state] = dict()
            self.p_dict[state] = dict()
            self.q_dict[state] = dict()
            for curr_input in self.base_fsm.states[state].keys():
                tran = self.base_fsm.states[state][curr_input]
                if is_salt:
                    # salt
                    self.derive_salt_file_for_transition(state, curr_input, j, N)
                    # run curr_salt_file_name
                    time_file_name = "/srv/salt/time_files/out_test_" + str(j) + ".out"
                    time_file = open(time_file_name, 'w')
                    salt_short_name = "salt_files/out_test_" + str(j)
                    salt_command = "salt \"*\" state.apply " + str(salt_short_name) + " > " + str(time_file_name)
                    command = ["sudo", "sh", "-c", salt_command]
                    # print(command)
                    process = subprocess.run(command, shell=False, capture_output=True, text=True)
                    (fluctuation_list, delay_list) = self.extract_times_salt(time_file_name, state)
                else:
                    # ansible
                    curr_ansible_file_name = self.derive_ansible_file_for_transition(state, curr_input, j, N)
                    time_file_name = "out_time.txt"
                    time_file = open(time_file_name, 'r')
                    (fluctuation_list, delay_list) = self.extract_times_ansible(time_file_name, state)
                self.u_dict[state][curr_input] = min(fluctuation_list)
                self.v_dict[state][curr_input] = max(fluctuation_list)
                self.p_dict[state][curr_input] = min(delay_list)
                self.q_dict[state][curr_input] = max(delay_list)
                min_delays[curr_input].append(float(self.p_dict[state][curr_input]))
                max_delays[curr_input].append(float(self.p_dict[state][curr_input]))
                j += 1
                u = float(self.u_dict[state][curr_input])
                v = float(self.v_dict[state][curr_input])
                if "send" in curr_input:
                    d = float(self.p_dict[state][curr_input])
                else:
                    d = float(self.q_dict[state][curr_input])
                print("tran.i =", tran.i)
                timed_tran = TimedTransition(tran.start_state, tran.i, u, v, tran.o, d, tran.end_state)
                timed_tran.print()
                self.base_fsm.states[state][curr_input] = timed_tran
        for i in self.base_fsm.fsm_inputs:
            self.min_p[i] = min(min_delays[i])
            self.max_q[i] = max(max_delays[i])
        for i in self.base_fsm.fsm_inputs:
            print(i, ": ", self.min_p[i])
            print(i, ": ", self.max_q[i])
        return

    def extract_times_ansible(self, time_file_name, state):
        with open(time_file_name, 'r') as file:
            content = file.read()
        started_dict = dict()
        duration_dict = dict()
        j = 0
        step = len(self.base_fsm.cover_set[state]) + 1
        start_pattern = re.compile(r'"start": "([^"]+)"')
        end_pattern = re.compile(r'"end": "([^"]+)"')
        plays = content.split('PLAY')
        play_durations = list()
        for play in plays[1:]:  # Skip the first split part as it's before the first PLAY
            start_times = start_pattern.findall(play)
            end_times = end_pattern.findall(play)
            if start_times and end_times:
                # Convert strings to datetime objects
                start_time_first = datetime.strptime(start_times[0], "%Y-%m-%d %H:%M:%S.%f")
                end_time_last = datetime.strptime(end_times[-1], "%Y-%m-%d %H:%M:%S.%f")
                # Calculate duration
                duration = end_time_last - start_time_first
                started_dict[j] = start_time_first
                duration_dict[j] = duration
                j += 1
        print("started_dict =", started_dict)
        print("duration_dict =", duration_dict)
        fluctuation_list = list()
        delay_list = list()
        for i in range(2 * step - 1, j, step):
            timestamp = started_dict[i] - started_dict[i - 1]
            total_seconds = timestamp.seconds + (timestamp.microseconds / 1000000)
            delay = duration_dict[i].seconds + (duration_dict[i].microseconds / 1000000)
            fluctuation_list.append(total_seconds)
            delay_list.append(delay)
        print("fluctuation_list =", fluctuation_list)
        print("delay_list =", delay_list)
        return (fluctuation_list, delay_list)

    def extract_times_salt(self, time_file_name, state):
        #time_file = open("time_out/out_test_7.out", 'r')
        time_file = open(time_file_name, 'r')
        started_dict = dict()
        duration_dict = dict()
        j = 0
        step = len(self.base_fsm.cover_set[state]) + 1
        #print("step =", step)
        for line in time_file:
            if 'Started' in line:
                started_time = line.split(' ')[6]
                time_obj = datetime.strptime(started_time.strip(), "%H:%M:%S.%f")
                #print("time_obj =", time_obj)
                started_dict[j] = time_obj
            if 'Duration' in line:
                duration = float(line.split(':')[1].strip().split(' ')[0])
                duration_dict[j] = duration
                j += 1
        #print("started_dict =", started_dict)
        #print("duration_dict =", duration_dict)
        fluctuation_list = list()
        delay_list = list()
        #print("j =", j)
        #for i in range(step-1, j+1, step):
        for i in range(2*step-1, j,step):
            timestamp = started_dict[i] - started_dict[i-1]
            timestamp_obj = datetime.strptime(str(timestamp), "%H:%M:%S.%f")
            total_milliseconds = (timestamp_obj.hour * 3600000) + (timestamp_obj.minute * 60000) + (timestamp_obj.second * 1000) + (timestamp_obj.microsecond / 1000)
            delay = duration_dict[i]
            fluctuation_list.append(total_milliseconds)
            delay_list.append(delay)
        #print("fluctuation_dict =", fluctuation_list)
        #print("delay_dict =", delay_list)
        return (fluctuation_list, delay_list)

    def print_in_tfsm_format(self):
        s_number = len(self.base_fsm.states.keys())
        i_number = len(self.base_fsm.fsm_inputs)
        o_number = len(self.base_fsm.fsm_outputs)
        t_number = s_number * i_number
        f_line = "F 0\n"
        print(f_line)
        #file.write(f_line)
        s_line = "s " + str(s_number) + "\n"
        print(s_line)
        #file.write(s_line)
        i_line = "i " + str(i_number) + "\n"
        print(i_line)
        #file.write(i_line)
        o_line = "o " + str(o_number) + "\n"
        print(o_line)
        #file.write(o_line)
        n0_line = "n0 0\n"
        print(n0_line)
        #file.write(n0_line)
        t_line = "p " + str(t_number) + "\n"
        print(t_line)
        #file.write(t_line)
        for curr_state_vec in self.base_fsm.hashed_states_dict:
            curr_state = self.base_fsm.hashed_states_dict[curr_state_vec]
            for i in self.base_fsm.fsm_inputs:
                timed_tran = self.base_fsm.states[curr_state.derive_vector()][i]
                timed_tran.print()
        return
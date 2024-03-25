import copy
from ansible import *
from saltstack import *

vm1_in = ["vm1_open", "vm1_close", "vm1_allow_sub_2", "vm1_deny_sub_2", "vm1_send_vm2", "vm1_send_vm3"]
vm2_in = ["vm2_open", "vm2_close", "vm2_allow_sub_2", "vm2_deny_sub_2", "vm2_send_vm1", "vm2_send_vm3"]
vm3_in = ["vm3_open", "vm3_close", "vm3_allow_sub_1", "vm3_deny_sub_1", "vm3_send_vm1", "vm3_send_vm2"]
inputs = vm1_in + vm2_in + vm3_in
outputs = ["0", "1", "2", "3", "4", "5", "6"]

class State:
    def __init__(self, state_bits, values_vec):
        self.state = dict()
        for i in range(0, len(state_bits)):
            self.state[state_bits[i]] = values_vec[i]
        return

    def satisfy_criterium(self, conditions):
        for cond in conditions:
            if self.state[cond] == 0:
                return False
        return True

    def derive_vector(self):
        self.vector = ""
        for st in self.state.keys():
            self.vector = self.vector + str(self.state[st])
        return self.vector

    def print(self):
        # print(self.vector)
        print(self.state)
        return

    def __eq__(self, other):
        if not isinstance(other, State):
            return NotImplemented
        else:
            return self.state == other.state

class Transition:
    def __init__(self, start_state, i, o, end_state):
        self.start_state = copy.deepcopy(start_state)
        self.i = str(i)
        self.o = str(o)
        self.end_state = copy.deepcopy(end_state)
        self.tran = [self.start_state.derive_vector(), self.i, self.end_state.derive_vector(), self.o]
        return

    def print(self):
        # print(self.tran)
        s_start_vec = self.start_state.derive_vector()
        s_start = int(s_start_vec, 2)
        i = inputs.index(self.i)
        s_end_vec = self.end_state.derive_vector()
        s_end = int(s_end_vec, 2)
        out_line = str(s_start) + ' ' + str(i) + ' ' + str(s_end) + ' ' + str(self.o)
        print(out_line)
        return

class FSM:
    def __init__(self, input_file):
        self.input_file = str(input_file)
        self.criteria = dict()
        self.states = dict()
        self.hashed_states_dict = dict()
        return

    def parse_inputs_outputs_states(self):
        in_file = open(self.input_file, 'r')
        inputs = in_file.readline()
        inputs = inputs[:-1]
        parsed_inputs = inputs.split(',')
        self.state_bits = list()
        self.contr_state_bits = dict()
        self.state_bits_contr_bits = dict()
        self.fsm_inputs = list()
        self.fsm_inputs_dict = dict()
        self.fsm_inputs_dict["deny"] = list()
        self.fsm_inputs_dict["allow"] = list()
        self.fsm_inputs_dict["impl"] = list()
        for item in parsed_inputs:
            pair = item.split('/')
            if len(pair) == 2:
                self.state_bits.append(pair[0])
                self.contr_state_bits[pair[1]] = str(pair[0])
                self.state_bits_contr_bits[pair[0]] = str(pair[1])
                self.fsm_inputs.append(pair[0])
                self.fsm_inputs_dict["allow"].append(pair[0])
                self.fsm_inputs.append(pair[1])
                self.fsm_inputs_dict["deny"].append(pair[1])
            else:
                self.fsm_inputs.append(item)
                self.fsm_inputs_dict["impl"].append(item)
        self.fsm_outputs = list()
        self.fsm_outputs.append('n')
        initial_vector = [0 for j in range(0, len(self.state_bits))]
        self.initial_state = State(self.state_bits, initial_vector)
        for line in in_file:
            line_list = line.split(':')
            self.fsm_outputs.append(line_list[0])
            line_list_2 = line_list[1].split('>')
            pred_conds = str(line_list_2[0][1:-1])
            pred_conds_list = pred_conds.split(',')
            post_cond = str(line_list_2[1][:-1])
            self.criteria[line_list[0]] = (pred_conds_list, post_cond)
            print(self.criteria[line_list[0]])
        return

    def derive_time_estimation_playbooks(self, playbook_file_name, estimation_times):
        playbook = Ansible_playbook(playbook_file_name, estimation_times)
        for in_command in self.fsm_inputs_dict["deny"]:
            playbook.add_task(in_command, 0)
        for i in range(0, playbook.estimation_times):
            for in_command in self.fsm_inputs_dict["allow"]:
                playbook.add_task(in_command, 1)
            for in_command in self.fsm_inputs_dict["impl"]:
                playbook.add_task(in_command, 1)
            for in_command in self.fsm_inputs_dict["deny"]:
                playbook.add_task(in_command, 1)
        playbook.collect_playbook()
        return

    def derive_fsm_bfs(self):
        queue = list()
        self.cover_set = dict()
        self.cover_set[self.initial_state.derive_vector()] = list()
        covered_states = list()
        covered_states.append(self.initial_state.derive_vector())
        visited_states = list()
        queue.append(self.initial_state)
        while len(queue) > 0:
            curr_state = queue.pop()
            self.states[curr_state.derive_vector()] = dict()
            self.hashed_states_dict[curr_state.derive_vector()] = copy.deepcopy(curr_state)
            visited_states.append(curr_state.derive_vector())
            for i in self.fsm_inputs:
                out = 0
                end_state = copy.deepcopy(curr_state)
                if i in self.state_bits:
                    end_state.state[i] = "1"
                elif i in self.contr_state_bits.keys():
                    end_state.state[self.contr_state_bits[i]] = "0"
                for conn in self.criteria.keys():
                    if i == self.criteria[conn][1]:
                        if curr_state.satisfy_criterium(self.criteria[conn][0]):
                            out = self.fsm_outputs.index(conn)
                input = self.fsm_inputs.index(i)
                tran = Transition(curr_state, input, out, end_state)
                self.states[curr_state.derive_vector()][i] = tran
                if not (end_state.derive_vector() in visited_states):
                    queue.append(end_state)
                if not (end_state.derive_vector() in covered_states):
                    covered_states.append(end_state.derive_vector())
                    self.cover_set[end_state.derive_vector()] = list(self.cover_set[curr_state.derive_vector()]) + [i]
        print(self.cover_set)
        return

    def print_ext(self):
        for curr_state_vec in self.hashed_states_dict:
            print("########")
            curr_state = self.hashed_states_dict[curr_state_vec]
            #curr_state.print()
            for i in self.fsm_inputs:
                print("--------")
                tran = self.states[curr_state.derive_vector()][i]
                print("start_state =", end='')
                tran.start_state.print()
                print("input =", i)
                print("output =", self.fsm_outputs[int(tran.o)])
                print("end_state =", end='')
                tran.end_state.print()
        return

    def calculate_timed_parmeters(self):
        return

    def derive_reversed_fsm(self):
        self.states_reversed = dict()
        for curr_state_vec in self.hashed_states_dict:
            self.states_reversed[curr_state_vec] = dict()
        for curr_state_vec in self.hashed_states_dict:
            curr_state = self.hashed_states_dict[curr_state_vec]
            for i in self.fsm_inputs:
                tran = self.states[curr_state.derive_vector()][i]
                end_state_vector = tran.end_state.derive_vector()
                self.states_reversed[end_state_vector][i] = tran
        return

    def print_in_fsm_format(self, fsm_file):
        file = open(fsm_file, 'w')
        s_number = len(self.states.keys())
        i_number = len(self.fsm_inputs)
        o_number = len(self.fsm_outputs)
        t_number = s_number * i_number
        f_line = "F 0\n"
        file.write(f_line)
        s_line = "s " + str(s_number) + "\n"
        file.write(s_line)
        i_line = "i " + str(i_number) + "\n"
        file.write(i_line)
        o_line = "o " + str(o_number) + "\n"
        file.write(o_line)
        n0_line = "n0 0\n"
        file.write(n0_line)
        t_line = "p " + str(t_number) + "\n"
        file.write(t_line)
        for curr_state_vec in self.hashed_states_dict:
            curr_state = self.hashed_states_dict[curr_state_vec]
            for i in self.fsm_inputs:
                tran = self.states[curr_state.derive_vector()][i]
                start_state_number = int(tran.start_state.derive_vector(), 2)
                i_number = str(tran.i)
                o_number = str(tran.o)
                end_state_number = int(tran.end_state.derive_vector(), 2)
                line = str(start_state_number) + ' ' + str(i_number) + ' ' + str(end_state_number) + ' ' + str(o_number) + '\n'
                file.write(line)
                #print(line)
        return
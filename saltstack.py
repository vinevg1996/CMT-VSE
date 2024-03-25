class SaltStack:
    def __init__(self, fsm_inputs):
        self.salt_states = dict()
        self.inputs = list(fsm_inputs)
        for curr_in in self.inputs:
            if "open" in curr_in:
                self.salt_states[curr_in] = dict()
                self.salt_states[curr_in]["name"] = "open_port_12345_"
                self.salt_states[curr_in]["command"] = "  iptables.append:\n"
                self.salt_states[curr_in]["command"] += "    - table: filter\n"
                self.salt_states[curr_in]["command"] += "    - chain: INPUT\n"
                self.salt_states[curr_in]["command"] += "    - jump: ACCEPT\n"
                self.salt_states[curr_in]["command"] += "    - match: state\n"
                self.salt_states[curr_in]["command"] += "    - connstate: NEW\n"
                self.salt_states[curr_in]["command"] += "    - dport: 12345\n"
                self.salt_states[curr_in]["command"] += "    - proto: tcp\n"
                self.salt_states[curr_in]["command"] += "    - save: True\n"
            elif "close" in curr_in:
                self.salt_states[curr_in] = dict()
                self.salt_states[curr_in]["name"] = "open_close_12345_"
                self.salt_states[curr_in]["command"] = "  iptables.append:\n"
                self.salt_states[curr_in]["command"] += "    - table: filter\n"
                self.salt_states[curr_in]["command"] += "    - chain: INPUT\n"
                self.salt_states[curr_in]["command"] += "    - jump: DROP\n"
                self.salt_states[curr_in]["command"] += "    - dport: 12345\n"
                self.salt_states[curr_in]["command"] += "    - proto: tcp\n"
                self.salt_states[curr_in]["command"] += "    - save: True\n"
            elif "allow" in curr_in:
                self.salt_states[curr_in] = dict()
                self.salt_states[curr_in]["name"] = "allow_traffic_from_192_168_122_1_on_port_12345_"
                self.salt_states[curr_in]["command"] = "  cmd.run:\n"
                self.salt_states[curr_in]["command"] += "    - name: |\n"
                self.salt_states[curr_in]["command"] += "        iptables -F INPUT  # Flush the INPUT chain to remove DROP and LOG rules for simplicity\n"
                self.salt_states[curr_in]["command"] += "        iptables -A INPUT -p tcp --dport 12345 -j ACCEPT  # Accept packets intended for port 12345\n"
                self.salt_states[curr_in]["command"] += "        iptables-save\n"
            elif "deny" in curr_in:
                self.salt_states[curr_in] = dict()
                self.salt_states[curr_in]["name"] = "deny_traffic_from_192_168_122_1_on_port_12345_"
                self.salt_states[curr_in]["command"] = "  iptables.append:\n"
                self.salt_states[curr_in]["command"] += "    - table: filter\n"
                self.salt_states[curr_in]["command"] += "    - chain: INPUT\n"
                self.salt_states[curr_in]["command"] += "    - source: 192.168.122.1\n"
                self.salt_states[curr_in]["command"] += "    - dport: 12345\n"
                self.salt_states[curr_in]["command"] += "    - proto: tcp\n"
                self.salt_states[curr_in]["command"] += "    - jump: DROP\n"
                self.salt_states[curr_in]["command"] += "    - save: True\n"
            elif "send" in curr_in:
                self.salt_states[curr_in] = dict()
                self.salt_states[curr_in]["name"] = "echo_hello_to_port_12345_"
                self.salt_states[curr_in]["command"] = "  cmd.run:\n"
                self.salt_states[curr_in]["command"] += "    - name: echo \"Hello\" | nc -q 0 localhost 12345\n"
        return

    def dervie_salt_state_for_a_trace(self, trace, repeat):
        j = 0
        trace_states = dict()
        saltState = "{% for i in range(" + str(repeat) + ") %}\n"
        for curr_in in trace:
            saltState += self.salt_states[curr_in]["name"] + str(j) + "_{{ i }}:\n"
            saltState += self.salt_states[curr_in]["command"]
            saltState += "\n"
            j += 1
        saltState += "{% endfor %}"
        return saltState

    def dervie_salt_state_for_a_timed_trace(self, timed_trace, repeat):
        j = 0
        trace_states = dict()
        saltState = "{% for i in range(" + str(repeat) + ") %}\n"
        t0 = 0.0
        for (curr_in, t) in timed_trace:
            sleep_time = int(t) - int(t0)
            saltState += self.salt_states[curr_in]["name"] + str(j) + "_{{ i }}:\n"
            saltState += self.salt_states[curr_in]["command"]
            saltState += "timeout_example:\n"
            saltState += "  cmd.run:\n"
            saltState += "    - name: sleep " + str(sleep_time) + "\n"
            saltState += "\n"
            j += 1
        saltState += "{% endfor %}"
        return saltState

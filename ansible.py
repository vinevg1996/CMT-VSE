class Ansible_playbook:
    def __init__(self, playbook_file_name, estimation_times):
        self.playbook_file = open(playbook_file_name, 'w')
        self.playbook = []
        self.async_time = 10
        self.poll_status = 1
        self.estimation_times = int(estimation_times)
        return

    def collect_playbook(self):
        playbook_str = '\n'.join(self.playbook)
        self.playbook_file.write(playbook_str)
        return

    def add_task(self, in_command, number):
        command_list = in_command.split('_')
        if command_list[1] == "open":
            self.add_open_task(command_list[0], number)
        if command_list[1] == "close":
            self.add_close_task(command_list[0], number)
        if command_list[1] == "allow":
            self.add_allow_task(command_list[0], command_list[2], number)
        if command_list[1] == "deny":
            self.add_deny_task(command_list[0], command_list[2], number)
        if command_list[1] == "send":
            self.add_send_task(command_list[0], command_list[2], number)
        return

    def add_open_task(self, vm, number):
        command_name = "Estimate " + str(vm) + "_open " + str(number)
        file = "/tmp/received_message_12345_" + str(number) + ".txt"
        self.playbook.append(
                "- name: " + str(command_name) + "\n"
                "  hosts: " + str(vm) + "\n"
                "  become: yes\n"
                "  tasks:\n"
                "  - name: " + str(command_name) + "_1\n"
                "    shell: netstat -an | grep 12345\n"
                "    register: netcat_check_" + str(vm) + "_" + str(number) + "\n"
                "    async: " + str(self.async_time) + "\n"
                "    poll: " + str(self.poll_status) + "\n"
                "    ignore_errors: yes\n"
                "\n"
                "  - name: " + str(command_name) + "_2\n"
                "    shell: nohup nc -lk 12345 >> " + str(file) + " &\n"
                "    async: 10\n"
                "    poll: 1\n"
                "    ignore_errors: true\n"
                "    when: netcat_check_" + str(vm) + "_" + str(number) + ".rc != 0\n\n")
        return

    def add_close_task(self, vm, number):
        command_name = "Estimate " + str(vm) + "_close " + str(number)
        self.playbook.append(
            "- name: " + str(command_name) + "\n"
            "  hosts: " + str(vm) + "\n"
            "  become: yes\n"
            "  tasks:\n"
            "  - name: " + str(command_name) + "_1\n"
            "    shell: \"lsof -i :12345 -t\"\n"
            "    register: nc_pid_" + str(number) + "\n"
            "    async: " + str(self.async_time) + "\n"
            "    poll: " + str(self.poll_status) + "\n"
            "    ignore_errors: yes\n"
            "\n"
            "  - name: " + str(command_name) + "_2\n"
            "    shell: \"kill -9 {{ nc_pid_" + str(number) + ".stdout }}\"\n"
            "    async: " + str(self.async_time) + "\n"
            "    poll: " + str(self.poll_status) + "\n"
            "    ignore_errors: yes\n"
            "    when: nc_pid_" + str(number) + ".stdout != \"\"\n\n")
        return

    def add_allow_task(self, vm, sub, number):
        command_name = "Estimate " + str(vm) + "_allow " + str(number)
        self.playbook.append(
            "- name: " + str(command_name) + "\n"
            "  hosts: " + str(vm) + "\n"
            "  become: yes\n"
            "  tasks:\n"
            "  - name: " + str(command_name) + "_1\n"
            "    command: iptables -D INPUT -s 192.168.233.255 -j DROP\n")
        return

    def add_deny_task(self, vm, sub, number):
        command_name = "Estimate " + str(vm) + "_deny " + str(number)
        self.playbook.append(
            "- name: " + str(command_name) + "\n"
            "  hosts: " + str(vm) + "\n"
            "  become: yes\n"
            "  tasks:\n"
            "  - name: " + str(command_name) + "_1\n"
            "    command: iptables -C INPUT -s 192.168.233.255 -j DROP\n"
            "    register: rule_check" + str(number) + "\n"
            "    async: " + str(self.async_time) + "\n"
            "    poll: " + str(self.poll_status) + "\n"
            "    ignore_errors: yes\n"
            "\n"
            "  - name: " + str(command_name) + "_2\n"
            "    command: iptables -A INPUT -s 192.168.233.255 -j DROP\n"
            "    async: " + str(self.async_time) + "\n"
            "    poll: " + str(self.poll_status) + "\n"
            "    ignore_errors: yes\n"
            "    when: rule_check" + str(number) + " is failed\n\n")
        return

    def add_send_task(self, vm1, vm2, number):
        command_name = "Estimate " + str(vm1) + "_send " + str(vm2) + ' ' + str(number)
        self.playbook.append(
            "- name: " + str(command_name) + "\n"
            "  hosts: " + str(vm1) + "\n"
            "  tasks:\n"
            "  - name: " + str(command_name) + "_1\n"
            "    shell: echo \"Hello_" + str(number) + "\" | nc -q 0 192.168.233.115 12345\n"
            "    async: " + str(self.async_time) + "\n"
            "    poll: " + str(self.poll_status) + "\n"
            "    ignore_errors: yes\n")
        return
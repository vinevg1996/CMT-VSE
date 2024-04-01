# CMT-VSE

**CMT-VSE** is a framework designed for model-based testing and verification of configuration management tools (CMTs). It provides tenant requests with timed recommendations for their safe execution.

## Overview

**CMT-VSE** takes three inputs:

1. **CMT Requirements:** Given as pre-post conditions describing the expected behavior of a CMT. Examples can be found in the "tests" directory.
2. **Implementation of a CMT:** Represented by files such as `ansible.py` and `saltstack.py`, which contain mappings of commands from input files to corresponding commands for Ansible and SaltStack, respectively. It is necessary to assign IP addresses and ports to relevant components.
3. **Tenant Request:** Defined by the `trace` variable in the `demo` function.

## Output

The **CMT-VSE** framework returns recommended timeouts for the safe execution of the tenant request specified in the `trace` variable.

## Functions

### fsm_class.py

Contains the FSM representation.

- **parse_inputs_outputs_states:** Parses input files.
- **derive_fsm_bfs:** Derives the specification FSM.
- **print_in_fsm_format:** Returns the specification FSM in .fsm format for further use with the Libfsmtest library for test-suite derivation.
- **derive_time_estimation_playbooks:** Returns TFSM modeling the CMT of interest.

### ansible.py and saltstack.py

Contain the conversion of abstract inputs from the input file to Ansible playbooks.

### tfsm_class.py

Contains the TFSM representation.

- **refine_tfsm:** Takes the TFSM and returns it with a safe execution property. If the specification FSM preserves pre-post conditions for an input sequence, then there exists a timed extension of the input sequence that preserves pre-post conditions.
- **derive_a_safe_trace:** Returns a safe trace for the input trace.

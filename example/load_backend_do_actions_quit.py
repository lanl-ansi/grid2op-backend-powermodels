import numpy as np
from grid2op.Backend import PandaPowerBackend
from grid2op.Action import BaseAction  # internal
import pdb
tol = 1e-4

# load the backend
backend = PandaPowerBackend()  # all backend should be created like this
backend.load_grid("matpower_case5.json")  # this method has to be implemented
# NB the format of data can change of course :-)
# i converted it using pandapower converter to .mat using
# "pandapower.converter.to_mpc" (https://pandapower.readthedocs.io/en/v1.2.0/converter/matpower.html)

# we'll worry later on how to handle multiple files ;-)

## internal and performed automatically
backend.set_env_name("example")  # this has not to be implemented

# now we list all "set" data
# but first we need to create the object that will allow to interact with the backend
from grid2op.Action._BackendAction import _BackendAction  # internal
bk_class = _BackendAction.init_grid(backend)  # internal, done automatically
env_to_backend = bk_class()   # internal, done automatically
action_class = BaseAction.init_grid(backend)   # internal, done automatically
my_action = action_class()   # internal, done automatically

# do a powerflow
print("TEST MAKE POWERFLOW...")
converged = backend.runpf()  # need to be implemented
assert converged

# I reading back the data
print("TEST READ DATA...")
prod_p, prod_q, prod_v = backend.generators_info()  # this method has to be implemented
# it gives the values for each generator, and put it all to a vector
assert np.all(np.abs(prod_p - [10., 21.72983]) <= tol)

load_p, load_q, laod_v = backend.loads_info()  # this method has to be implemented
# it gives the values for each loads, and put it all to a vector
assert np.all(np.abs(load_q -[7., 7., 7.]) <= tol)

p_or, q_or, v_or, a_or = backend.lines_or_info()  # this method has to be implemented
# it gives the values for each lines (origin end), and put it all to a vector
assert np.all(np.abs(v_or - [102., 102., 102., 102., 102., 101.92142, 101.92142, 101.86371]) <= tol)

p_ex, q_ex, v_ex, a_ex = backend.lines_ex_info()  # this method has to be implemented
# it gives the values for each lines (extremity end), and put it all to a vector
assert np.all(np.abs(a_ex - [343.28632, 164.39331, 109.338905,  95.58921, 322.761 ,75.67738,  75.67738,  54.05088]) <= tol)

# now i change the value of the generators for example
print("TEST CHANGE GENERATOR...")
my_action = action_class()   # internal, done automatically
my_action.update({"injection": {"prod_p": [prod_p[0] + 1., prod_p[1] -1.]}})  # internal, this is done by "an agent"
print(my_action)  # print what the action is doing
env_to_backend += my_action  # internal, this is done by "the environment"
# this is the env_to_backend action that is interesting, and most notably the "prod_p_setpoint" , you can inspect prod_p.changed, prod_p.values
# active_bus, (prod_p_setpoint, prod_v_setpoint, load_p_setpoint, load_q_setpoint), topo__, shunts__ = env_to_backend()
# I invite you to look at the following code
backend.apply_action(env_to_backend)  # this method has to be implemented
converged = backend.runpf()  # need to be implemented
assert converged
prod_p_1, prod_q_1, prod_v_1 = backend.generators_info()  # this method has to be implemented
assert np.all(np.abs(prod_p_1 - [11., 20.482985]) <= tol)  # NB in this case, the losses of the grid have been reduced
# that is why prod_p_1[1] != prod_p[1] -1.

# I change the loads q (then run a powerflow and check they are correct)
print("TEST CHANGE LOAD...")
my_action = action_class()   # internal, done automatically
env_to_backend.reset()  # internal, this is done by "the environment"
new_load_q = [load_q[0] + 2.,  load_q[1] -2., load_q[2]]  # internal, this is done by "an agent"
my_action.update({"injection": {"load_q": new_load_q}})  # internal, this is done by "an agent"
env_to_backend += my_action  # internal, this is done by "the environment"
# this is the env_to_backend action that is interesting, and most notably the "load_q", you can inspect load_q.changed, load_q.values
backend.apply_action(env_to_backend)  # this method has to be implemented
print(my_action)  # print what the action is doing
converged = backend.runpf()  # need to be implemented
assert converged
load_p_2, load_q_2, load_v_2 = backend.loads_info()  # this method has to be implemented
assert np.all(np.abs(load_q_2 - new_load_q) <= tol)
# that is why prod_p_1[1] != prod_p[1] -1.

# now i disconnect a powerline
print("TEST DISCONNECT LINE...")
line_id = 0
my_action = action_class()   # internal, done automatically
env_to_backend.reset()  # internal, this is done by "the environment"
my_action.update({"set_line_status": [(line_id, -1)]})  # internal, this is done by "an agent"
env_to_backend += my_action  # internal, this is done by "the environment"
# this is the env_to_backend action that is interesting, and most notably the "topo__", you can inspect topo__.changed, topo__.values
backend.apply_action(env_to_backend)  # this method has to be implemented
print(my_action)  # print what the action is doing
converged = backend.runpf()  # need to be implemented
assert converged
p_or_3, q_or_3, v_or_3, a_or_3 = backend.lines_or_info()  # this method has to be implemented
assert p_or_3[line_id] == 0.
assert q_or_3[line_id] == 0.
assert a_or_3[line_id] == 0.
# the following should be true, but that's a bug we did not catch...
# assert v_or_3[line_id] == 0.  # see https://github.com/rte-france/Grid2Op/issues/70

# finally a test that changes the topology of substation 2
# before that, let's represent it
# this substation has 4 elements to it:
# powerline 1 extremity
# powerline 4 extemity
# powerline 6 origin
# powerline 7 origin
# at beginning the are all connected to the same busbar, say "busbar 1"
# this action will put powerline 1 and 6 on busbar 1 and powerline 4 and 7 on busbar 2
# this could correspond to the oppening of a coupling breaker between busbar 1 and busbar2
print("TEST CHANGE TOPOLOGY...")
line_id = 0
my_action = action_class()   # internal, done automatically
env_to_backend.reset()  # internal, this is done by "the environment"
my_action.update({"set_bus": {"lines_or_id": [(6, 2)], "lines_ex_id": [(4, 2)]}})  # internal, this is done by "an agent"
env_to_backend += my_action  # internal, this is done by "the environment"
# this is the env_to_backend action that is interesting, and most notably the "topo__", you can inspect topo__.changed, topo__.values
backend.apply_action(env_to_backend)  # this method has to be implemented
print(my_action)
converged = backend.runpf()  # need to be implemented
assert converged
p_or_4, q_or_4, v_or_4, a_or_4 = backend.lines_or_info()  # this method has to be implemented
assert p_or_4[4] != p_or_3[4]  # flow on powerline 4 has changed obviously
assert np.all(np.abs(p_or_4 - [ 0., -1.3701046, -1.5593017,  3.9294062, 25.859959, -1.9127275, 23.611242,  6.740214]) <= tol)

# and a utility in grid2op, that you don't need to re implement, even allows you to check that your grid (as seen by
# grid2op meet the kirchoff's law or not)
sum_p_by_sub, sum_q_by_sub, sum_p_by_busbar, sum_q_by_busbar = backend.check_kirchoff()
assert np.all(np.abs(sum_p_by_busbar) <= tol)
assert np.all(np.abs(sum_q_by_busbar) <= tol)
print("all tests have passed")
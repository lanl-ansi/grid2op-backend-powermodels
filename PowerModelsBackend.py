import os  # load the python os default module
import sys  # laod the python sys default module
import copy
import warnings
import subprocess


from grid2op.dtypes import dt_int, dt_float, dt_bool
from grid2op.Backend.Backend import Backend
from grid2op.Action import BaseAction
from grid2op.Exceptions import *


class PowerModelsBackend(Backend):
    def __init__(self, detailed_infos_for_cascading_failures=False):
        Backend.__init__(self, detailed_infos_for_cascading_failures=detailed_infos_for_cascading_failures)

        print("starting julia...")
        self._julia_process = subprocess.Popen(
            "julia --project=.. -e 'include(\"../PowerModelsBackend.jl\"); interactive_mode()'",
            shell=True,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
        )

        while True:
            sys.stdout.flush()
            self._julia_process.stdout.flush()
            output = self._julia_process.stdout.readline()
            if output.startswith("waiting for input line...") or self._julia_process.poll() is not None:
                break
            if output:
                print(output.strip())
        print("julia process ready for input")

        # complilation run
        print("starting julia complilation")
        result = self._run_julia_backend_command("load_grid, data/case5.m")
        result = self._run_julia_backend_command("run_ac_pf")
        result = self._run_julia_backend_command("run_dc_pf")
        result = self._run_julia_backend_command("reset")

        print("julia complilation complete, PowerModelsBackend ready")


    def _run_julia_backend_command(self, command):
        if self._julia_process.poll() is not None:
            print("process has terminated skipping julia command: ", command)

        print("sending command to julia: {}".format(command))
        sys.stdout.flush()
        sys.stderr.flush()

        self._julia_process.stdin.write(command)
        self._julia_process.stdin.write("\n")
        self._julia_process.stdin.flush()

        results = []
        while True:
            sys.stdout.flush()
            output = self._julia_process.stdout.readline()
            if output.startswith("waiting for input line...") or self._julia_process.poll() is not None:
                break
            else:
                results.append(output.strip())

        print("julia command complete")

        if len(results) != 2:
            print("\033[91mbad backend output, incorrect number of lines, {}\033[0m".format(len(results)))
            return []

        if results[1] != "complete":
            print("\033[91mbad backend output, status value {}, see process stderr for details\033[0m".format(results[1]))
            return []

        return results[0]


    # def get_nb_active_bus(self):
    #     """
    #     Compute the amount of buses "in service" eg with at least a powerline connected to it.

    #     Returns
    #     -------
    #     res: :class:`int`
    #         The total number of active buses.
    #     """
    #     return np.sum(self._grid.bus["in_service"])

    def reset(self, path=None, filename=None):
        """
        Reload the grid.
        For pandapower, it is a bit faster to store of a copy of itself at the end of load_grid
        and deep_copy it to itself instead of calling load_grid again
        """
        result = self._run_julia_backend_command("reset")

    def load_grid(self, path=None, filename=None):
        """
        Load the _grid, and initialize all the member of the class. Note that in order to perform topological
        modification of the substation of the underlying powergrid, some buses are added to the test case loaded. They
        are set as "out of service" unless a topological action acts on these specific substations.
        """

        if path is None and filename is None:
            raise RuntimeError("You must provide at least one of path or file to laod a powergrid.")
        if path is None:
            full_path = filename
        elif filename is None:
            full_path = path
        else:
            full_path = os.path.join(path, filename)
        if not os.path.exists(full_path):
            raise RuntimeError("There is no powergrid at \"{}\"".format(full_path))

        result = self._run_julia_backend_command("load_grid, {}".format(full_path))

    def apply_action(self, action:BaseAction):
    #def apply_action(self, action):
        pass
        # """
        # Specific implementation of the method to apply an action modifying a powergrid in the pandapower format.
        # """

        # if not isinstance(action, BaseAction):
        #     raise UnrecognizedAction("BaseAction given to PowerModelsBackend should be of class BaseAction and not "
        #                              "\"{}\"".format(action.__class__))

        # # change the _injection if needed
        # dict_injection, set_status, switch_status, set_topo_vect, switcth_topo_vect, redispatching, shunts = action()

        # for k in dict_injection:
        #     if k in self._vars_action_set:
        #         tmp = self._get_vector_inj[k](self._grid)
        #         val = 1. * dict_injection[k]
        #         ok_ind = np.isfinite(val)
        #         if k == "prod_v":
        #             pass
        #             # convert values back to pu
        #             val /= self.prod_pu_to_kv  # self._grid.bus["vn_kv"][self._grid.gen["bus"]].values
        #             if self._id_bus_added is not None:
        #                 # in this case the slack bus where not modeled as an independant generator in the
        #                 # original data
        #                 if np.isfinite(val[self._id_bus_added]):
        #                     # handling of the slack bus, where "2" generators are present.
        #                     pass
        #                     self._grid["ext_grid"]["vm_pu"] = val[self._id_bus_added]
        #         tmp[ok_ind] = val[ok_ind]
        #     else:
        #         warn = "The key {} is not recognized by PowerModelsBackend when setting injections value.".format(k)
        #         warnings.warn(warn)

        # if np.any(redispatching != 0.):
        #     # print("before tmp[ok_ind]: {}".format(self._get_vector_inj["prod_p"](self._grid)))
        #     tmp = self._get_vector_inj["prod_p"](self._grid)
        #     ok_ind = np.isfinite(redispatching)
        #     tmp[ok_ind] += redispatching[ok_ind]
        #     # print("after tmp[ok_ind]: {}".format(self._get_vector_inj["prod_p"](self._grid)))

        # # shunts
        # if shunts:
        #     arr_ = shunts["shunt_p"]
        #     is_ok = np.isfinite(arr_)
        #     self._grid.shunt["p_mw"][is_ok] = arr_[is_ok]
        #     arr_ = shunts["shunt_q"]
        #     is_ok = np.isfinite(arr_)
        #     self._grid.shunt["q_mvar"][is_ok] = arr_[is_ok]

        #     arr_ = shunts["shunt_bus"]
        #     ## turn off turned off shunt
        #     turned_off = arr_ == -1
        #     self._grid.shunt["in_service"][turned_off] = False
        #     ## turn on turned on shunt
        #     turned_on = arr_ >= 1
        #     self._grid.shunt["in_service"][turned_on] = True

        #     ## assign proper buses (1 = subid, 2 = subid + n_sub)
        #     is_ok = arr_ > 0
        #     bus_shunt = self.shunt_to_subid[is_ok]
        #     bus_shunt[(arr_ == 2)[is_ok]] += self.n_sub
        #     self._grid.shunt["bus"][is_ok] = bus_shunt

        # # topology
        # # run through all substations, find the topology. If it has changed, then update it.
        # beg_ = 0
        # end_ = 0
        # possiblechange = set_topo_vect != 0
        # if np.any(possiblechange) or np.any(switcth_topo_vect):
        #     actual_topo_full = self.get_topo_vect()
        #     if np.any(set_topo_vect[possiblechange] != actual_topo_full[possiblechange]) or np.any(switcth_topo_vect):
        #         for sub_id, nb_obj in enumerate(self.sub_info):
        #             nb_obj = int(nb_obj)
        #             end_ += nb_obj
        #             # extract all sub information
        #             this_topo_set = set_topo_vect[beg_:end_]
        #             this_topo_switch = switcth_topo_vect[beg_:end_]
        #             actual_topo = copy.deepcopy(actual_topo_full[beg_:end_])
        #             origin_topo = copy.deepcopy(actual_topo_full[beg_:end_])

        #             # compute topology after action
        #             if np.any(this_topo_switch):
        #                 # i need to switch some element
        #                 st = actual_topo[this_topo_switch]  # st is between 1 and 2
        #                 st -= 1  # st is between 0 and 1
        #                 st *= -1  # st is 0 or -1
        #                 st += 2  # st is 2 or 1 (i switched 1 <-> 2 compared to the original values)
        #                 actual_topo[this_topo_switch] = st
        #             if np.any(this_topo_set != 0):
        #                 # some buses have been set
        #                 sel_ = (this_topo_set != 0)
        #                 actual_topo[sel_] = this_topo_set[sel_]

        #             # in case the topo vector is 2,2,2 etc. i convert it back to 1,1,1 etc.
        #             actual_topo = actual_topo - np.min(actual_topo[actual_topo > 0.]) + 1
        #             # implement in on the _grid
        #             # change the topology in case it doesn"t match the original one
        #             if np.any(actual_topo != origin_topo):
        #                 nb_bus_before = len(np.unique(origin_topo[origin_topo > 0.]))  # only count activated bus
        #                 nb_bus_now = len(np.unique(actual_topo[actual_topo > 0.]))  # only count activated bus
        #                 if nb_bus_before > nb_bus_now:
        #                     # i must deactivate the unused bus
        #                     self._grid.bus["in_service"][sub_id + self.n_sub] = False
        #                 elif nb_bus_before < nb_bus_now:
        #                     # i must activate the new bus
        #                     self._grid.bus["in_service"][sub_id + self.n_sub] = True

        #                 # now assign the proper bus to each element
        #                 for i, (table, col_name, row_id) in enumerate(self._what_object_where[sub_id]):
        #                     self._grid[table][col_name].iloc[row_id] = sub_id if actual_topo[i] == 1 else sub_id + self.n_sub
        #                     # if actual_topo[i] <0:
        #                     #     pdb.set_trace()
        #                     # self._grid[table][col_name].iloc[i] = sub_id if actual_topo[i] == 1 else sub_id + self.n_sub

        #             beg_ += nb_obj

        # # change line status if needed
        # # note that it is a specification that lines status must override buses reconfiguration.
        # if np.any(set_status != 0.):
        #     for i, el in enumerate(set_status):
        #         # TODO performance optim here, it can be vectorized
        #         if el == -1:
        #             self._disconnect_line(i)
        #         elif el == 1:
        #             self._reconnect_line(i)

        # # switch line status if needed
        # if np.any(switch_status):
        #     for i, el in enumerate(switch_status):
        #         # TODO performance optim here, it can be vectorized
        #         df = self._grid.line if i < self._number_true_line else self._grid.trafo
        #         tmp = i if i < self._number_true_line else i - self._number_true_line

        #         if el:
        #             connected = df["in_service"].iloc[tmp]
        #             if connected:
        #                 df["in_service"].iloc[tmp] = False
        #             else:
        #                 bus_or = set_topo_vect[self.line_or_pos_topo_vect[i]]
        #                 bus_ex = set_topo_vect[self.line_ex_pos_topo_vect[i]]
        #                 if bus_ex == 0 or bus_or == 0:
        #                     raise InvalidLineStatus("Line {} was disconnected. The action switched its status, "
        #                                             "without providing buses to connect it on both ends.".format(i))
        #                 # reconnection has then be handled in the topology
        #                 df["in_service"].iloc[tmp] = True


    def runpf(self, is_dc=False):
        """
        Run a power flow on the underlying _grid. This implements an optimization of the powerflow
        computation: if the number of
        buses has not changed between two calls, the previous results are re used. This speeds up the computation
        in case of "do nothing" action applied.
        """

        if not is_dc:
            result = self._run_julia_backend_command("run_ac_pf")
        else:
            result = self._run_julia_backend_command("run_dc_pf")

        if result.strip().lower() == "true":
            return True

        return False

    # TODO required by abstract class
    def copy(self):
        """
        Performs a deep copy of the power :attr:`_grid`.
        As pandapower is pure python, the deep copy operator is perfectly suited for the task.
        """
        assert(False)
        # res = copy.deepcopy(self)
        # return res

    # TODO required by abstract class
    def close(self):
        """
        Called when the :class:`grid2op;Environment` has terminated, this function only reset the grid to a state
        where it has not been loaded.
        """
        assert(False)
        # del self._grid
        # self._grid = None

    # def save_file(self, full_path):
    #     """
    #     Save the file to json.
    #     :param full_path:
    #     :return:
    #     """
    #     pp.to_json(self._grid, full_path)

    # TODO required by abstract class
    def get_line_status(self):
        """
        As all the functions related to powerline, pandapower split them into multiple dataframe (some for transformers,
        some for 3 winding transformers etc.). We make sure to get them all here.
        """
        assert(False)
        #return np.concatenate((self._grid.line["in_service"].values, self._grid.trafo["in_service"].values)).astype(dt_bool)

    # TODO required by abstract class
    def get_line_flow(self):
        """
        return the powerflow in amps in all powerlines.
        :return:
        """
        assert(False)
        #return self.a_or

    # TODO required by abstract class
    def _disconnect_line(self, id):
        assert(False)
        # if id < self._number_true_line:
        #     self._grid.line["in_service"].iloc[id] = False
        # else:
        #     self._grid.trafo["in_service"].iloc[id - self._number_true_line] = False

    # TODO required by abstract class
    def get_topo_vect(self):
        assert(False)
        # res = np.full(self.dim_topo, fill_value=np.NaN, dtype=dt_int)

        # line_status = self.get_line_status()

        # i = 0
        # for row in self._grid.line[["from_bus", "to_bus"]].values:
        #     bus_or_id = row[0]
        #     bus_ex_id = row[1]
        #     if line_status[i]:
        #         res[self.line_or_pos_topo_vect[i]] = 1 if bus_or_id == self.line_or_to_subid[i] else 2
        #         res[self.line_ex_pos_topo_vect[i]] = 1 if bus_ex_id == self.line_ex_to_subid[i] else 2
        #     else:
        #         res[self.line_or_pos_topo_vect[i]] = -1
        #         res[self.line_ex_pos_topo_vect[i]] = -1
        #     i += 1

        # nb = self._number_true_line
        # i = 0
        # for row in self._grid.trafo[["hv_bus", "lv_bus"]].values:
        #     bus_or_id = row[0]
        #     bus_ex_id = row[1]

        #     j = i + nb
        #     if line_status[j]:
        #         res[self.line_or_pos_topo_vect[j]] = 1 if bus_or_id == self.line_or_to_subid[j] else 2
        #         res[self.line_ex_pos_topo_vect[j]] = 1 if bus_ex_id == self.line_ex_to_subid[j] else 2
        #     else:
        #         res[self.line_or_pos_topo_vect[j]] = -1
        #         res[self.line_ex_pos_topo_vect[j]] = -1
        #     i += 1

        # i = 0
        # for bus_id in self._grid.gen["bus"].values:
        #     res[self.gen_pos_topo_vect[i]] = 1 if bus_id == self.gen_to_subid[i] else 2
        #     i += 1

        # i = 0
        # for bus_id in self._grid.load["bus"].values:
        #     res[self.load_pos_topo_vect[i]] = 1 if bus_id == self.load_to_subid[i] else 2
        #     i += 1

        # return res

    # TODO required by abstract class
    def generators_info(self):
        assert(False)
        #return self.prod_p, self.prod_q, self.prod_v

    # TODO required by abstract class
    def loads_info(self):
        assert(False)
        #return self.load_p, self.load_q, self.load_v

    # TODO required by abstract class
    def lines_or_info(self):
        assert(False)
        #return self.p_or, self.q_or, self.v_or, self.a_or

    # TODO required by abstract class
    def lines_ex_info(self):
        assert(False)
        #return self.p_ex, self.q_ex, self.v_ex, self.a_ex

    # def shunt_info(self):
    #     shunt_p = 1.0 * self._grid.res_shunt["p_mw"].values
    #     shunt_q = 1.0 * self._grid.res_shunt["q_mvar"].values
    #     shunt_v = self._grid.res_bus["vm_pu"].values[self._grid.shunt["bus"].values]
    #     shunt_v *= self._grid.bus["vn_kv"].values[self._grid.shunt["bus"]]
    #     shunt_bus = self._grid.shunt["bus"].values
    #     return shunt_p, shunt_q, shunt_v, shunt_bus

    # def sub_from_bus_id(self, bus_id):
    #     if bus_id >= self._number_true_line:
    #         return bus_id - self._number_true_line
    #     return bus_id

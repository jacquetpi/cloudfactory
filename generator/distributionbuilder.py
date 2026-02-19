"""Build VM flavor sets from a distribution scenario (YAML).

Loads CPU and memory flavor frequencies from YAML; generates lists of VmModel
either to match a target VM count or to match target total CPU and memory using
optimization (SLSQP) while respecting the distribution.
"""
import yaml
import scipy.optimize
import numpy as np
from generator.vmmodel import *

class DistributionBuilder(object):
    """
    A class used to build a set of VM according to a scenario features (config and usage)
    ...

    Attributes
    ----------
    config_cpu : dict
        cpu config (flavor) distribution
    config_mem : dict
        mem config (flavor) distribution

    Public Methods
    -------
    generate_set_from_vm_number(number_of_vm : int):
        Generate a list of scenario-compliant VMs of the requested count.
    generate_set_from_config(cpu : int, mem : int):
        Generate a list of scenario-compliant VMs matching target CPU and memory totals.
    """

    def __init__(self, **kwargs):
        required_attributes = ["yaml_file"]
        for required_attribute in required_attributes:
            if required_attribute not in kwargs: raise ValueError("Missing required attributes", required_attribute, "in", required_attributes)
        self.__load_from_yaml(kwargs["yaml_file"])
    
    def __load_from_yaml(self, yaml_file : str):
        """Initiate attributes from yaml config file

        Parameters
        ----------
        yaml_file : str
            Yaml file location

        Raises
        ------
        ValueError
            If sum of frequencies are not equals to 1
        """

        with open(yaml_file, 'r') as file:
            yaml_as_dict = yaml.full_load(file)
            
        distribution = yaml_as_dict["vm_distribution"]
        self.config_cpu = distribution["config_cpu"]
        self.config_mem = distribution["config_mem"]
        
        if round(sum(self.config_cpu.values()),2) > 1.0:
            print("Warning : CPU distribution frequency exceeded 1")
            self.config_cpu = self.__reduce_freq_to_one(self.config_cpu)

        if round(sum(self.config_mem.values()),2) > 1.0: 
            print("Warning : Mem distribution frequency exceeded 1")
            self.config_mem = self.__reduce_freq_to_one(self.config_mem)

    def generate_set_from_vm_number(self, number_of_vm : int, display : bool = True):
        """ Generate a list of n (number_of_vm) VMs while respecting builder constraints

        Parameters
        ----------
        number_of_vm : int
            number of requested VM
        display : bool 
            Display information to the operator
        """
        flavor_list = list()
        for cpu_flavor, cpu_freq in self.config_cpu.items():
            number_of_required_vms = int(cpu_freq*number_of_vm)
            flavor_list.extend([(cpu_flavor, None) for x in range(number_of_required_vms)])

        self.__update_flavor_mem_distribution(flavor_list=flavor_list) # Update list with memory intel
        vm_list = self.__generate_set_from_flavor_list(flavor_list)
        if display: self.__display_list(vm_list)
        return vm_list

    def generate_set_from_config(self, cpu : int, mem : int, display : bool = True):
        """ Generate a list of VM from the cpu and memory node configuration while respecting builder constraints

        Parameters
        ----------
        cpu : int
            number of virtual CPU available
        mem : int
            number of Go available
        display : bool 
            Display information to the operator
        """
        flavor_list = self.__generate_flavor_cpu_distribution(cpu=cpu) # Generate list of flavor with CPU intel
        self.__update_flavor_mem_distribution(flavor_list=flavor_list) # Update list with memory intel
        vm_list = self.__generate_set_from_flavor_list(flavor_list)
        if display: self.__display_list(vm_list, cpu, mem)
        return vm_list

    def __generate_flavor_cpu_distribution(self, cpu : int):
        """ Generate list of potential VM as a list of tuple (cpu, mem) where mem is not initialized. 
        List is generated with a research operational approach where we maximise CPU usage while respecting VM size distribution

        Parameters
        ----------
        cpu : int
            number of virtual CPU available

        Returns
        -------
        flavor_list
            list of tuple (cpu, mem) where mem is None
        """
        flavor_list=list()
        
        bnds, xinit, func, cons = self.__generate_operations_research_problem_for_cpu(cpu)

        results = scipy.optimize.minimize(func, x0=xinit, bounds=bnds, constraints=cons, method='SLSQP') # options={'disp': True}
        i=0
        ordered_cpu_flavor = list(self.config_cpu.keys())
        ordered_cpu_flavor.sort()
        for val in results['x']:
            # we generate a couple (cpu,mem) for each on-going VM (mem is not initialised yet, so None)
            flavor_list+= [(ordered_cpu_flavor[i], None) for j in range(round(val))]
            i+=1

        return flavor_list

    def __generate_operations_research_problem_for_cpu(self, cpu : int):
        """ Convert object attributes (representing VM size distribution and frequency) to an operational research question
        We want to minimize the number of unused CPU (the maximum is passed as a parameter) while respecting specified distribution

        Parameters
        ----------
        cpu : int
            number of virtual CPU available

        Returns
        -------
        bnds : list
            scipy optimise bounds
        xinit : list
            scipy init values
        func : lamnda
            scipy maximising objective
        cons : list
            scipy minimising objectiveS
        """
        distro_count = len(self.config_cpu.keys())

        # Bound
        bnds = [(1, cpu) for i in range(distro_count)]
        # Init 
        xinit = [1 for i in range(distro_count)]

        eval_func = ""
        i=0
        for cpu_flavor in self.config_cpu.keys():
            if i>0: eval_func += " + "
            eval_func += "x[" + str(i) + "]*" + str(cpu_flavor)
            i+=1

        # Minimize unused cpu, maximize use cpu
        minimize_func_eval = "lambda x: " + str(cpu) + " - " + eval_func
        maximize_func_eval = "lambda x: " +  eval_func + " - " + str(cpu)

        func = eval(maximize_func_eval)

        # ADD constraint about VM size frequency in distribution : we minimize :  "x[i]/(np.sum(x)) - f"
        cons = list()
        cons.append({'type': 'ineq', 'fun': eval(maximize_func_eval)})
        i=0
        for cpu_freq in self.config_cpu.values():
            local_eval_func = "lambda x: x[" + str(i) + "]/(np.sum(x)) - " + str(cpu_freq)
            cons.append({'type': 'ineq', 'fun': eval(local_eval_func) })
            i+=1
        
        return bnds, xinit, func, cons


    def __update_flavor_mem_distribution(self, flavor_list : list):
        """ Update flavor_list with memory distribution based on scenario (config_mem)

        Parameters
        ----------
        flavor_list : list
            list of tuple (cpu, mem) where mem is to be updated

        """

        # Based on scenario, we compute the count of VM for each memory flavor
        vm_total = len(flavor_list)
        ordered_mem_flavor = list(self.config_mem.keys())
        ordered_mem_flavor.sort()
        mem_config_count_per_type= list()
        for mem_flavor in ordered_mem_flavor:
            associated_number_of_vm = round(self.config_mem[mem_flavor]*vm_total)
            if mem_flavor == ordered_mem_flavor[-1]: associated_number_of_vm = vm_total # To handle round values on last iteration
            mem_config_count_per_type.append((associated_number_of_vm, mem_flavor))

        mem_index=0
        mem_config_count, current_alloc = mem_config_count_per_type[mem_index]
        for i in range(vm_total):
            flavor_list[i] = (flavor_list[i][0], current_alloc) # Update config list with memory flavor
            mem_config_count-=1
            if(mem_config_count <= 0):
                mem_index+=1
                mem_config_count, current_alloc = mem_config_count_per_type[mem_index]

    def __generate_set_from_flavor_list(self, flavor_list : list):
        """ Generate a list of VM from a flavor list.

        Parameters
        ----------
        flavor_list : list
            list of flavor implemented
        """
        vm_list = list()
        for flavor_cpu, flavor_mem in flavor_list:
            vm_list.append(VmModel(cpu=flavor_cpu, mem=flavor_mem))
        return vm_list

    def __display_list(self, vm_list : list, cpu_objective : int = None, mem_objective : int = None):
        """ Print informations on generated vm list
        Parameters
        ----------
        vm_list : list
            list of VMs
        cpu_objective : int
            sum of cores specified at the generation
        mem_objective : int
            sum of mem specified at the generation step
        """
        display_dict = dict()
        for vm in vm_list:
            key = (vm.get_cpu(), vm.get_mem())
            if key not in display_dict: display_dict[key] = 0
            display_dict[key] += 1
        cpu_total, mem_total = (0,0)
        for config, count in display_dict.items():
            cpu_config, mem_config = config
            print(str(cpu_config) + "c-" + str(mem_config) + "gb :", count, "vm")
            cpu_total+=cpu_config*count
            mem_total+=mem_config*count
        print("Total VM", len(vm_list))
        print("Total vcpu", cpu_total) if cpu_objective is None else print("Total vcpu", cpu_total, "/", cpu_objective)
        print("Total mem", mem_total) if mem_objective is None else print("Total mem", mem_total, "/", mem_objective) 

    def __reduce_freq_to_one(self, dict_to_reduce):
        """ Reduce a dict of frequencies so its values are equals to one
        Parameters
        ----------
        dict_to_reduce : dict
            Dict of frequencies (key : config, value : freq)
        """
        print("Distribution was reduced as described:")
        original = dict(dict_to_reduce)
        delta = round(sum(dict_to_reduce.values()) - 1, 2)
        keys = list(dict_to_reduce.keys())
        keys.sort(reverse=True)
        while delta>0:
            key = keys.pop(0)
            if delta > original[key]:
                delta-= original[key]
                dict_to_reduce[key] = 0
            else:
                dict_to_reduce[key] = dict_to_reduce[key] - delta
                delta=0
        for key in dict_to_reduce.keys():
            print(key, ":", original[key], "->", dict_to_reduce[key])
        return dict_to_reduce
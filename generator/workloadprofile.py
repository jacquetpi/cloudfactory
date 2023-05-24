from generator.vmmodel import *
import math

class WorkloadProfile(object):
    """
    A class used to represent a specific workload profile
    ...

    Attributes
    ----------
    usage_profiles : dict
        Vm usage scenario

    Public Methods
    -------
    does_vm_verify_constraints(vm : VmModel):
       Test if a VM verify this workload profile constraints
    generate_and_apply_worload_commands(vm_list : list):
        Generate and apply commands list for each VM corresponding to its profile category
    """

    def __init__(self, name : str, workload_as_dict : dict, global_acronyms : dict, slice_duration : int):
        self.name = name
        interpreted_command = workload_as_dict["command"]
        # Interpret static acronyms
        for acronym, replacement in global_acronyms.items():
            interpreted_command = interpreted_command.replace(acronym, replacement) 
        self.command = interpreted_command
        self.dynamic_acronyms = workload_as_dict["acronyms"] if "acronyms" in workload_as_dict else dict()
        self.constraint = workload_as_dict["constraint"]
        self.slice_duration = slice_duration

    def does_vm_verify_constraints(self, vm : VmModel):
        """ Test if a VM verify this workload profile constraints
        Parameters
        ----------
        vm : VmModel
            Vm to be tested on workload profile constraints

        Returns
        -------
        result : bool
            True if constraints are respected, false otherwise
        """
        if "profile" in self.constraint:
            if vm.get_profile() not in self.constraint["profile"]: 
                return False
        if "mem" in self.constraint:
            if "min" in self.constraint["mem"] and vm.get_mem() < self.constraint["mem"]["min"]:
                return False
            if "max" in self.constraint["mem"] and vm.get_mem() > self.constraint["mem"]["max"]:
                return False
        if "cpu" in self.constraint:
            if "min" in self.constraint["cpu"] and vm.get_cpu() < self.constraint["cpu"]["min"]:
                return False
            if "max" in self.constraint["cpu"] and vm.get_cpu() > self.constraint["cpu"]["max"]:
                return False
        return True

    def generate_and_apply_worload_commands(self, vm_list : list):
        """Generate and apply commands list for each VM corresponding to its profile category
        Parameters
        ----------
        vm_list : list
            list of VM to be updated
        """
        filtered_list = self.__filter_list(vm_list)
        for vm in filtered_list:
            self.__generate_commands_from_vm_usage(vm)

    def __generate_commands_from_vm_usage(self, vm : VmModel):
        """Retrieve VM usage list and generate commands list based on it
        Generated commands list is set as a vm attribute
        ----------
        vm : VmModel
            vm targeted
        """
        commands_list = list()
        for targeted_usage in vm.get_usage():
            commands_list.append(self.__generate_command(vm, targeted_usage))
        vm.set_commands_list(commands_list)

    def __generate_command(self, vm : VmModel, targeted_usage : int):
        """Generate a command by interpreting static and dynamic acronyms
        ----------
        targeted_usage : int
            CPU Targeted usage

        Returns
        -------
        command : str
            the generated command       
        """
        # Interpret and evaluate standard dynamic acronyms
        command = self.__replace_standard_dynamic_acronyms(self.command, vm, targeted_usage)
        # Interpret and evaluate custom dynamic acronyms
        command = self.__replace_custom_dynamic_acronyms(command, vm, targeted_usage)
        return command

    def __replace_standard_dynamic_acronyms(self, command : str, vm : VmModel, targeted_usage : int):
        """Replace in specified command standard dynamic acronym
        /!\ exception is §name, managed by VmModel object as we may want to change identifier based on local or remote access
        ----------
        command : str
            Command to be interpreted
        targeted_usage : int
            CPU Targeted usage

        Returns
        -------
        command : str
            the generated command       
        """
        custom_command = command.replace("§time", str(self.slice_duration))
        custom_command = custom_command.replace("§cpu", str(vm.get_cpu()))
        custom_command = custom_command.replace("§mem", str(vm.get_mem()))
        return custom_command.replace("§target", str(targeted_usage))

    def __replace_custom_dynamic_acronyms(self, command : str, vm : VmModel, targeted_usage : int):
        """Replace in specified command custom dynamic acronym
        ----------
        command : str
            Command to be interpreted
        targeted_usage : int
            CPU Targeted usage

        Returns
        -------
        command : str
            the generated command       
        """
        dynamic_values_evaluated = dict()
        # Interpret dynamically generated acronyms
        for key, dynamic_value in self.dynamic_acronyms.items():
            value_interpreted = self.__replace_standard_dynamic_acronyms(dynamic_value, vm, targeted_usage)
            value_evaluated = eval(value_interpreted)
            dynamic_values_evaluated[key] = str(value_evaluated)
        # Replace dynamically generated acronyms
        targeted_command = str(command)
        for key, final_value in dynamic_values_evaluated.items():
            targeted_command = targeted_command.replace(key, final_value)
        return targeted_command

    def __filter_list(self, vm_list):
        """ Return list of VM with the same workload name as the current instance.
        Parameters
        ----------
        vm_list : list
            list of VM
        """
        return [vm for vm in vm_list if vm.get_workload() == self.name]

    def get_freq(self):
        return self.constraint["freq"]
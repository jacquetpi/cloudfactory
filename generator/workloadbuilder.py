import yaml, math, random
from generator.workloadprofile import WorkloadProfile

class WorkloadBuilder(object):
    """
    A class used to attribute workload to each VM
    After attribution, commands are generated with WorkloadProfile objects
    ...

    Attributes
    ----------
    acronyms : dict
        static acronyms (key/value to be exchange in command generation)
    vm_workloads : dict
        WorkloadProfile object dict

    Public Methods
    -------
    attribute_workload_commands_to_vm_list
        Generate workload commands for each VM
    get_context
        acronym getter
    """
    def __init__(self, **kwargs):
        required_attributes = ["yaml_file", "slice_duration"]
        for required_attribute in required_attributes:
            if required_attribute not in kwargs: raise ValueError("Missing required attributes", required_attribute, "in", required_attributes)
        self.slice_duration = kwargs["slice_duration"]
        self.__load_from_yaml(kwargs["yaml_file"])

    def __load_from_yaml(self, yaml_file : str):
        with open(yaml_file, 'r') as file:
            yaml_as_dict = yaml.full_load(file)

        vm_workloads = yaml_as_dict["vm_workloads"]

        if sum([x["constraint"]["freq"] for x in vm_workloads["workloads"].values()]) > 1: raise ValueError("Usage distribution frequency sum must be equal to one ")

        self.acronyms = vm_workloads["acronyms"] if "acronyms" in vm_workloads else dict()
        self.workloads = dict()
        for workload_name, workload_dict in vm_workloads["workloads"].items():
            self.workloads[workload_name] = WorkloadProfile(workload_name, workload_dict, self.acronyms, self.slice_duration)
    
    def attribute_workload_commands_to_vm_list(self, vm_list : list):
        """Generate workload commands for each VM
        /!\ VM must have a usage previously attributed

        Parameters
        ----------
        vm_list : list
            list of VMs : VM object will be updated with workload
        """
        # Update VM attributes
        self.__attribute_workloads_to_vm_list(vm_list)
        for workload in self.workloads.values():
            workload.generate_and_apply_worload_commands(vm_list)

    def __attribute_workloads_to_vm_list(self, vm_list : list):
        """Attribute given workloads to each VM

        Parameters
        ----------
        vm_list : list
            list of VMs : VM object will be updated with workload
        """
        total_number_of_vm = len(vm_list)
        workload_to_treat = list(self.workloads.keys())
        treated_workload = list()
        treated_vm = list()
        
        while workload_to_treat:

            conform_list = self.__generate_conform_vm_list_per_workload(vm_list, vm_to_exlude=treated_vm, workload_to_exclude=treated_workload)
            if len(conform_list) <=0:
                #print("Warning : Unable to deploy following workloads to profile set due to low number of VM or constraints", workload_to_treat)
                break

            conform_list_count = {workload_name : len(conform_list[workload_name]) for workload_name in conform_list.keys()}
            # Treat more restrictive workload
            min_workload = min(conform_list_count, key=lambda k: conform_list_count[k])
            required_vm = math.ceil(self.workloads[min_workload].get_freq()*total_number_of_vm)
            attributed_vm = self.__attribute_specific_workload_to_conform_list(min_workload, conform_list[min_workload], required_vm)
            
            # Update loop data
            workload_to_treat.remove(min_workload)
            treated_workload.append(min_workload)
            treated_vm.extend(attributed_vm)
        
        not_treated = list() # Rare case : if workloads constraint did not match the number of VMs
        for vm in vm_list: 
            if vm not in treated_vm: not_treated.append(vm)
        if not_treated: self.__attribute_workloads_to_vm_list(not_treated)

    def __attribute_specific_workload_to_conform_list(self, workload_name : str, conform_vm : list(), required_vm : int):
        """Attribute specified workload to n (required_vm attribute) randomly pick VM in conform_vm list

        Parameters
        ----------
        workload_name : str
            The workload identifier to be attributed
        conform_vm : list
            list of potential VM (may be larger than required vm number)
        required_vm : int
            the number of VM requested to have this workload

        Returns
        -------
        attributed_vm : list
            list of VM attributed to this workload
        """
        delta = len(conform_vm) - required_vm
        if delta < 0:
            # print("Could not fullfil workload attribution due to constraints on", workload_name, "required:", required_vm, "available:", len(conform_vm))
            required_vm = len(conform_vm)
            random_list = list()
        else:
            random_list = [False for i in range(delta)]
        random_list.extend([True for i in range(required_vm)])
        random.shuffle(random_list)
        attributed_vm = list()
        for vm_index, is_attributed in enumerate(random_list):
            if is_attributed:
                conform_vm[vm_index].set_workload(workload_name)
                attributed_vm.append(conform_vm[vm_index])
        return attributed_vm

    def __generate_conform_vm_list_per_workload(self, vm_list : int, vm_to_exlude = list(), workload_to_exclude = list()):
        """ Generate a list of conform VM per workload. As workload may have individual constraints,
        this list may change from one to one
        ----------
        number_of_profile : int
            Number of profile to be generated
        vm_to_exlude : list
            list of VM to ignore
        workload_to_exclude : list
            list of workload to ignore

        Returns
        -------
        profile_list : list
            list of profile name
        """
        workload_conformity_list = dict()
        for vm in vm_list:
            if vm in vm_to_exlude: 
                continue
            for workload_name, workload_profile in self.workloads.items():
                if workload_name in workload_to_exclude: 
                    continue
                if workload_profile.does_vm_verify_constraints(vm):
                    if workload_name not in workload_conformity_list:
                        workload_conformity_list[workload_name] = list()
                    workload_conformity_list[workload_name].append(vm)
        return workload_conformity_list

    def get_context(self, acronym : str):
        """ Getter to access static acronym
        acronym : str
            acronym to be accessed (without § )

        Returns
        -------
        value : str
            value of acronym
        """
        if "§" not in acronym:
            acronym = "§" + acronym
        return self.acronyms[acronym]
import yaml, random, math
from cloudfactory.vmmodel import *
from cloudfactory.usageprofile import *
from cloudfactory.vmusagebuilder import VmUsageBuilder

class UsageBuilder(object):
    """
    A class used to attribute VMs a usage profile based on scenario
    After attribution, usage can be generated 
    ...

    Attributes
    ----------
    usage_profiles : dict of UsageProfile
        Vm Profile (category of usage)
    vm_usage_builder = VmUsageBuilder
        Object used to compute usage based on profile

    Public Methods
    -------
    attribute_usage_to_vm_list(vmlist : list, postponed_start : int):
       Update a list of VM with randomly selected usage profile
    get_overall_count_of_vm_to_be_created():
        return the number of VM to be created on each scope based on profiles
    """

    def __init__(self, **kwargs):
        required_attributes = ["yaml_file", 'slices_per_scope', 'number_of_scope']
        for required_attribute in required_attributes:
            if required_attribute not in kwargs: raise ValueError("Missing required attributes", required_attribute, "in", required_attributes)
        self.slices_per_scope=kwargs["slices_per_scope"]
        self.number_of_scope=kwargs["number_of_scope"]
        self.profiles = dict()
        self.__load_from_yaml(kwargs["yaml_file"])
        self.vm_usage_builder = VmUsageBuilder(profiles=self.profiles, slices_per_scope=self.slices_per_scope)
    
    def __load_from_yaml(self, yaml_file : str):
        """Init attributes from yaml config file

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
        
        if sum([x["freq"] for x in yaml_as_dict["vm_profile"].values()]) > 1: raise ValueError("Usage distribution frequency sum must be equal to one ")

        for name, profile_as_dict in yaml_as_dict["vm_profile"].items():
            self.profiles[name] = UsageProfile(name, 
                profile_as_dict=profile_as_dict,
                slices_per_scope=self.slices_per_scope,
                number_of_scope=self.number_of_scope
                )

    def attribute_usage_to_vm_list(self, vm_list : list, postponed_scope_start : int = 0):
        """ Attribute usage (cpu usage) based on periodicity, lifetime, number of scopes
        ----------
        vm_list : list
            list of VMs to be updated
        postponed_scope_start : int
            Scope in which passed VMs are created
        """
        # Update VM attributes
        self.__attribute_profile_to_vm_list(vm_list)
        for profile in self.profiles.values():
            profile.generate_and_apply_usage(vm_list, postponed_scope_start)
        # Generate workload
        for vm in vm_list:
            self.vm_usage_builder.build_and_set_usage_for_VM(vm)

    def get_overall_count_of_vm_to_be_created(self):
        """ Based on profiles arrival rate, return the amount of new VMs to be created

        Returns
        -------
        count : int
            number of VM to be created at each scope
        """
        count = 0
        for profile in self.profiles.values(): 
            count+= profile.get_count_of_vm_to_be_created()
        return count

    def __attribute_profile_to_vm_list(self, vm_list : list):
        """ Update a list of VM with randomly selected profile
        Profile can be seen as an abstracted category of usage
        ----------
        vm_list : list
            list of VMs
        """
        profile_list = self.__generate_profile_list(number_of_profile=len(vm_list))
        for count, vm in enumerate(vm_list):
            vm.set_profile(profile_list[count])

    def __generate_profile_list(self, number_of_profile : int):
        """ Generate a list of profile. List is shuffled to avoid even distribution on a same set of VM
        Parameters
        ----------
        number_of_profile : int
            Number of profile to be generated

        Returns
        -------
        profile_list : list
            list of profile name
        """
        profile_list = list()
        for profile_id, profile_data in self.profiles.items():
            count_for_specific_profile = math.ceil(number_of_profile*profile_data.get_freq())
            profile_list.extend([profile_id for x in range(count_for_specific_profile)])
        random.shuffle(profile_list)
        return profile_list

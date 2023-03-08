import yaml, random, math
from cloudfactory.vmmodel import *
from cloudfactory.usageprofile import *
from cloudfactory.vmusagebuilder import VmUsageBuilder

class UsageBuilder(object):
    """
    A class used to attribute VMs a usage profile based on scenario
    ...

    Attributes
    ----------
    usage_profiles : dict
        Vm usage scenario

    Public Methods
    -------
    attribute_usage_to_vm_list(cpu : int, mem : int):
       Update a list of VM with randomly selected usage profile
    """

    def __init__(self, **kwargs):
        required_attributes = ["yaml_file"]
        for required_attribute in required_attributes:
            if required_attribute not in kwargs: raise ValueError("Missing required attributes", required_attributes)
        self.__load_from_yaml(kwargs["yaml_file"])
    
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
        
        if sum([x["freq"] for x in yaml_as_dict["vm_usage"].values()]) > 1: raise ValueError("Usage distribution frequency sum must be equal to one ")

        self.profiles = dict()
        for name, profile_as_dict in yaml_as_dict["vm_usage"].items():
            self.profiles[name] = UsageProfile(name, profile_as_dict)

        self.vm_usage_builder = VmUsageBuilder(self.profiles)

    def attribute_usage_to_vm_list(self, vm_list : list):
        """ Attribute usage (cpu usage) based on periodicity, lifetime, number of scopes
        ----------
        vm_list : list
            list of VMs
        """
        # Update VM attributes
        self.attribute_profile_to_vm_list(vm_list)
        for profile in self.profiles.values():
            profile.apply_usage_periodicity_to_vm_list(vm_list)
            profile.apply_usage_lifetime_to_vm_list(vm_list)
        # Generate workload
        # TODO: reprendre ici
        #for vm in vm_list:
        #self.vm_usage_builder.build_and_set_usage_for_VM(vm)

    def attribute_profile_to_vm_list(self, vm_list : list):
        """ Update a list of VM with randomly selected profile
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

    def get_overall_count_of_vm_to_be_created(self):
        """ Based on profiles arrival rate, return the amount of new VMs to be created

        Returns
        -------
        count : int
            number of VM to be created at each scope
        """
        count = 0
        for profile in self.profiles.values(): count+= profile.get_count_of_vm_to_be_created()
        return count

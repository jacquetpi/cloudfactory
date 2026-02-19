import yaml, random, math
from generator.vmmodel import *
from generator.usageprofile import *
from generator.vmusagebuilder import VmUsageBuilder
from generator.distributiongenerator import DistributionGenerator

class UsageBuilder(object):
    """
    Assigns usage profiles to VMs from a scenario and generates per-VM CPU usage over time.

    Loads usage profiles from a YAML scenario (frequencies, avg/per bounds, arrival/departure/
    periodicity rates). Assigns profiles to VMs, builds timesheets and periodicity, then uses
    VmUsageBuilder to generate concrete CPU usage lists.

    Attributes
    ----------
    profiles : dict
        Profile name -> UsageProfile (frequency, bounds, rates).
    vm_usage_builder : VmUsageBuilder
        Builds per-VM CPU usage from profile and timesheet.
    distribution_generator : DistributionGenerator
        Used for heavy-tail deployment spread over slices.

    Public Methods
    -------
    attribute_usage_to_vm_list(vm_list, postponed_scope_start=0)
        Assign profiles and generate usage and timesheets for the VM list.
    get_overall_count_of_vm_to_be_created()
        Return the number of new VMs to create per scope (from arrival rates).
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
        self.distribution_generator = DistributionGenerator()
    
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

        for name, profile_as_dict in yaml_as_dict["vm_usage"].items():
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
        postponed_dict = self.__convert_postpone_to_slice_list(vm_list, postponed_scope_start)
        for name, profile in self.profiles.items():
            profile.generate_and_apply_usage(vm_list, postponed_dict[name])
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
        delta = number_of_profile - len(profile_list)
        while delta>0: # manage rounded values
            for profile_id in self.profiles.keys():
                if delta <=0: break
                profile_list.append(profile_id)
                delta-=1
        random.shuffle(profile_list)
        return profile_list

    def __convert_postpone_to_slice_list(self, vm_list : list, postponed_scope_start : int):
        """ Convert postponed start to slices start for a VM list
        ----------
        vm_list : list
            list of VMs
        postponed_scope_start : int
            Scope in which passed VMs are created

        Returns
        -------
        slice_start_list_per_profile : dict
            Dict containing a list of randomised slice start per profile
        """
        slice_start_list_per_profile = dict()
        # First case : no postponed start
        if postponed_scope_start<=0:
            for name, profile in self.profiles.items():
                slice_start_list_per_profile[name] = [0 for x in range(profile.get_count(vm_list))]    
            return slice_start_list_per_profile
        # Second case : postponed start : we generate the number of VM to deploy per slice using an heavy tail gaussian
        slice_distribution = self.distribution_generator.generate_heavy_tail_gaussian_for_deployments(number_of_vms=len(vm_list),
            number_of_values=self.slices_per_scope)
        # Initialize lists
        profile_list = list()
        for name, profile in self.profiles.items():
            slice_start_list_per_profile[name] = list()
            profile_list.extend([name for x in range(profile.get_count(vm_list))])
        random.shuffle(profile_list)
        # Convert count to randomized slices start per profile:
        self.__distribute_start_through_profile(slice_distribution=slice_distribution, profile_list=profile_list, 
            profile_dict=slice_start_list_per_profile, postponed_scope_start=postponed_scope_start)
        return slice_start_list_per_profile

    def __distribute_start_through_profile(self, slice_distribution : list, profile_list : list, postponed_scope_start : int, profile_dict : dict):
        """Distribute VM start slices across profiles; profile_dict is updated in place.

        Parameters
        ----------
        slice_distribution : list
            Number of VMs to start per slice in the postponed scope.
        profile_list : list
            Randomly ordered profile names, one per VM.
        postponed_scope_start : int
            Scope index in which the VMs are created.
        profile_dict : dict
            Initialized dict profile_name -> list; each list gets slice start indices.
        """
        slice_distribution_count = list(slice_distribution)
        while profile_list:
            profile_to_start = profile_list.pop(0)
            valid_index = list()
            for index in range(len(slice_distribution_count)): 
                if slice_distribution_count[index] >0: valid_index.append(index)
            # Manage rounded values with a default value on max peak:
            if len(valid_index) == 0: valid_index.append(slice_distribution.argmax())
            # Choose index and manage counter
            chosen_index = valid_index[random.randrange(len(valid_index))]
            slice_distribution_count[chosen_index]-=1
            profile_dict[profile_to_start].append(chosen_index + (postponed_scope_start*self.slices_per_scope))
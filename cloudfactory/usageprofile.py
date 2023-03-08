import math, random

class UsageProfile(object):
    """
    A class used to represent a specific usage profile
    ...

    Attributes
    ----------
    usage_profiles : dict
        Vm usage scenario

    Public Methods
    -------
    apply_periodicity_to_vm_list(cpu : int, mem : int):
       Update a list of VM with randomly selected usage profile
    """

    def __init__(self, name : str, profile_as_dict : dict):
        self.name = name
        self.freq = profile_as_dict["freq"]
        self.average = profile_as_dict["avg"]
        self.percentile = profile_as_dict["per"]
        self.rate_departure = profile_as_dict["rate"]["departure"] if ("rate" in profile_as_dict and "departure" in profile_as_dict["rate"]) else 0.0
        self.rate_arrival = profile_as_dict["rate"]["arrival"] if ("rate" in profile_as_dict and "arrival" in profile_as_dict["rate"]) else 0.0
        self.rate_periodicity = profile_as_dict["rate"]["periodicity"] if ("rate" in profile_as_dict and "periodicity" in profile_as_dict["rate"]) else 0.0

    def apply_usage_periodicity_to_vm_list(self, vm_list):
        """Apply profile periodicity to a vm_list. Will only consider and update VM matching its usage profile name

        Parameters
        ----------
        vm_list : list
            list of VM to be updated
        """
        filtered_list = self.__filter_list(vm_list)
        periodic_count = math.floor(self.rate_periodicity*len(filtered_list))
        non_periodic_count = len(filtered_list) - periodic_count
        periodicity_list = [True for i in range(non_periodic_count)]
        periodicity_list.extend([False for i in range(non_periodic_count)])
        random.shuffle(periodicity_list)
        for count, vm in enumerate(filtered_list):
            vm.set_periodicity(periodicity_list[count])

    def apply_usage_lifetime_to_vm_list(self, vm_list):
        """Apply lifetime to a vm_list. Will only consider and update VM matching its usage profile name

        Parameters
        ----------
        vm_list : list
            list of VM to be updated
        """
        filtered_list = self.__filter_list(vm_list)
        # Based on Azure insights, a VM living more than a day is very likely to have a long lifetime
        # We therefore compute lifetime as a binary data : less or more than a day
        less_count = math.floor(self.rate_departure*len(filtered_list))
        more_count = len(filtered_list) - less_count
        lifetime_list = [1 for i in range(less_count)]
        lifetime_list.extend([0 for i in range(more_count)])
        random.shuffle(lifetime_list)
        for count, vm in enumerate(filtered_list):
            vm.set_lifetime(lifetime_list[count])


    def get_count_of_vm_to_be_created(self, number):
        """Apply arrival rate to deduct the number of new VMs at each scope

        Parameters
        ----------
        vm_list : number of initial VMs
            list of VM to be updated
        """
        if not hasattr(self, 'initial_vm_count'):
            raise ValueError("Initial VM count could not be deducated")
        return math.floor(self.rate_arrival*self.initial_vm_count)

    def __filter_list(self, vm_list):
        """ Return list of VM with the same profile name as the current instance.
        On first call, keep track of the initial VM count for later use
        Parameters
        ----------
        vm_list : number of initial VMs
            list of VM to be updated
        """
        filtered_list = [vm for vm in vm_list if vm.get_profile() == self.name]
        if not hasattr(self, 'initial_vm_count'):
            self.initial_vm_count = len(filtered_list)
        return filtered_list

    def get_average_bounds(self):
        return self.average["min"], self.average["max"]

    def get_percentile_bounds(self):
        return self.percentile["min"], self.percentile["max"]

    def get_freq(self):
        return self.freq
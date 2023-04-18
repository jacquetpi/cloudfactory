import math, random
from random import randrange
from generator.vmmodel import *

class UsageProfile(object):
    """
    A class used to represent a specific usage profile
    Profile can be seen as an abstracted category of usage
    ...

    Attributes
    ----------
    freq : int
        Profile attribution frequency
    average : dict
        average usage bounds
    percentile : dict
        percentile usage bounds
    rate_departure : float
        Profile departure rate
    rate_arrival : float
        Profile arrival rate
    rate_periodicity : float
        Profile periodicity rate
    slices_per_scope : int
        Context data : number of slices per scope in this experiment
    number_of_scope : int
        Context data : number of scope this experiment

    Public Methods
    -------
    generate_and_apply_usage(cpu : int, mem : int):
       Update a list of VM with usage generated from this profile
    """

    def __init__(self, name : str, profile_as_dict : dict, slices_per_scope : int, number_of_scope : int):
        self.name = name
        self.freq = profile_as_dict["freq"]
        self.average = profile_as_dict["avg"]
        self.percentile = profile_as_dict["per"]
        self.rate_departure = profile_as_dict["rate"]["departure"] if ("rate" in profile_as_dict and "departure" in profile_as_dict["rate"]) else 0.0
        self.rate_arrival = profile_as_dict["rate"]["arrival"] if ("rate" in profile_as_dict and "arrival" in profile_as_dict["rate"]) else 0.0
        self.rate_periodicity = profile_as_dict["rate"]["periodicity"] if ("rate" in profile_as_dict and "periodicity" in profile_as_dict["rate"]) else 0.0
        self.slices_per_scope=slices_per_scope
        self.number_of_scope=number_of_scope

    def generate_and_apply_usage(self, vm_list : list, postponed_start : list):
        """Generate and apply an usage (list of cpu usage) for each VM corresponding to its profile category
        Parameters
        ----------
        vm_list : list
            list of VM to be updated
        postponed_start : list
           list of randomized slices start for VM
        """
        filtered_list = self.__filter_list(vm_list)
        # Departure and arrival rate related
        self.__apply_usage_lifetime_to_vm_list(filtered_list, postponed_start)
        # Periodicity rate
        self.__apply_usage_periodicity_to_vm_list(filtered_list)

    def __apply_usage_periodicity_to_vm_list(self, filtered_list : list):
        """Apply profile periodicity to a vm_list

        Parameters
        ----------
        vm_list : list
            list of VM to be updated
        """
        periodic_count = math.floor(self.rate_periodicity*len(filtered_list))
        non_periodic_count = len(filtered_list) - periodic_count
        periodicity_list = [True for i in range(non_periodic_count)]
        periodicity_list.extend([False for i in range(non_periodic_count)])
        random.shuffle(periodicity_list)
        for count, vm in enumerate(filtered_list):
            vm.set_periodicity(periodicity_list[count])

    def __apply_usage_lifetime_to_vm_list(self, filtered_list : list, postponed_start : list):
        """Apply lifetime to a vm_list
        This method use the departure rate feature

        Parameters
        ----------
        vm_list : list
            list of VM to be updated
        postponed_start : list
            list of randomized slices start for VM
        """
        # Based on Azure insights, a VM living more than a day is very likely to have a long lifetime
        # We therefore compute lifetime as a binary data : less or more than a day
        less_count = math.floor(self.rate_departure*len(filtered_list))
        more_count = len(filtered_list) - less_count
        scope_lifetime_list = [1 for i in range(less_count)]
        scope_lifetime_list.extend([0 for i in range(more_count)])
        random.shuffle(scope_lifetime_list)
        for count, vm in enumerate(filtered_list):
            vm.set_postponed_start(postponed_start[count])
            vm.set_lifetime(self.__convert_scope_count_to_slice_count(scope_lifetime_list[count]))
            vm.set_timesheet(self.__generate_timesheet_for_vm(vm))
        
    def __generate_timesheet_for_vm(self, vm : VmModel):
        """Generate timesheet (presence intel on each slice) to a vm_list
        /!\ VM lifetime and VM start must be initialized before calling this method

        Parameters
        ----------
        vm : VmModel
            VM to be studied

        Return
        ----------
        timesheet : dict
            dict of scope, slices are represent by index in a list containing boolean values (True/False if vm is present)
        """
        # Initialize to False
        timesheet = dict()
        for scope in range(self.number_of_scope): 
            timesheet[scope] = [False for slices in range(self.slices_per_scope)]
        max_range = vm.get_postponed_start() + vm.get_lifetime() if vm.get_lifetime() > 0 else (self.number_of_scope*self.slices_per_scope)
        vm_range = range(vm.get_postponed_start(), max_range)
        # Check range
        count = 0
        for slices in timesheet.values():
            for index in range(len(slices)):
                if count in vm_range: slices[index] = True
                count+=1
        return timesheet

    def __convert_scope_count_to_slice_count(self, scope_count : int):
        """Convert a scope count to a slice count with a slight random factor to spread values

        Parameters
        ----------
        scope_count : int
            Count expressed as scope

        Return
        ----------
        slices : int
            Count expressed as slices
        """
        if scope_count <=0 : return 0
        return randrange(1,self.slices_per_scope+1)

    def get_count_of_vm_to_be_created(self):
        """Deduct the number of new VMs at each scope
        This method use the arrival rate feature

        Return
        ----------
        number : int
            Number of VMs to be created
        """
        if not hasattr(self, 'initial_vm_count'):
            raise ValueError("Initial VM count could not be inferred")
        return math.floor(self.rate_arrival*self.initial_vm_count)

    def __filter_list(self, vm_list):
        """ Return list of VM with the same profile name as the current instance.
        On first call, keep track of the initial VM count for later use
        Parameters
        ----------
        vm_list : list
            list of VM

        Return
        ----------
        filtered_list : list
            The filtered list
        """
        filtered_list = [vm for vm in vm_list if vm.get_profile() == self.name]
        if not hasattr(self, 'initial_vm_count'):
            self.initial_vm_count = len(filtered_list)
        return filtered_list

    def get_count(self, vm_list : list):
        """ Return count of VM matching current profile in list
        ----------
        vm_list : list
            list of VM

        Return
        ----------
        count : int
            Number of profile matching this profile
        """
        return len(self.__filter_list(vm_list))

    def get_average_bounds(self):
        return self.average["min"], self.average["max"]

    def get_percentile_bounds(self):
        return self.percentile["min"], self.percentile["max"]

    def get_freq(self):
        return self.freq
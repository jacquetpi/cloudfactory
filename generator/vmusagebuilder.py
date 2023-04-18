from generator.vmmodel import *
from generator.distributiongenerator import DistributionGenerator
import random, math

class VmUsageBuilder(object):
    """
    A class used to attribute VM usage based on their profile
    ...

    Attributes
    ----------
    profile : dict
        UsageProfile object dict
    slices_per_scope : int
        number of slices (virtual hours) per scope (virtual days)
    distribution_generator : DistributionGenerator
        Object used to generate gaussian distributions

    Public Methods
    -------
    build_and_set_usage_for_VM
        set for given VM its usage (list of CPU target values)
    """

    def __init__(self, profiles : dict, slices_per_scope : int):
        self.profiles = profiles
        self.slices_per_scope = slices_per_scope
        self.distribution_generator = DistributionGenerator()

    def build_and_set_usage_for_VM(self, vm : VmModel):
        """build a coherent (based on vm attributes) usage in the form of a list of cpu usage.
        List is set as a new attribute of VM
        /!\ VM attributes related to profile usage must be fully initialised

        Parameters
        ----------
        vm : VmModel
            VM to be updated
        """
        if(vm.is_periodic()):
            cpu_target_list = self.__generate_periodic_workload(vm=vm)
        else:
            cpu_target_list = self.__generate_nonperiodic_workload(vm=vm)
        vm.set_usage(cpu_target_list)

    def __generate_periodic_workload(self, vm : VmModel):
        """Build a periodic workload in the sense that cpu usage is reproduced through time

        Parameters
        ----------
        vm : VmModel
            VM to take into account

        Returns
        -------
        cpu_target : list
            list of cpu usage value
        """
        gaussian = self.__generate_gaussian_distribution_from_model(vm=vm)
        value_per_slice = list()
        for j in range(self.slices_per_scope):
            value_per_slice.append(self.__get_random_value_in(gaussian))
            
        cpu_target = list()
        timesheet = vm.get_timesheet()
        for scope in timesheet.values():
            for slice_index, slice_presence in enumerate(scope):
                if not slice_presence:
                    continue
                cpu_target.append(value_per_slice[slice_index])
        return cpu_target

    def __generate_nonperiodic_workload(self, vm : VmModel):
        """Build a non periodic workload in the sense that cpu usage values are randomly pick through time

        Parameters
        ----------
        vm : VmModel
            VM to take into account

        Returns
        -------
        cpu_target : list
            list of cpu usage value
        """
        gaussian = self.__generate_gaussian_distribution_from_model(vm=vm)
        cpu_target = list()
        timesheet = vm.get_timesheet()
        for scope in timesheet.values():
            for slice_index, slice_presence in enumerate(scope):
                if not slice_presence:
                    continue
                cpu_target.append(self.__get_random_value_in(gaussian))
        return cpu_target

    def __generate_gaussian_distribution_from_model(self, vm : VmModel):
        """Generate a gaussian distribution matching vm model specifications

        Parameters
        ----------
        vm : VmModel
            VM to take into account

        Returns
        -------
        x : list
            list of cpu usage value following a gaussian distribution
        """
        workload_cpu_avg, workload_cpu_per = self.__generate_avg_and_percentile(vm)
        return self.distribution_generator.generate_gaussian_distribution_from_avg(workload_cpu_avg, workload_cpu_per)

    def __generate_avg_and_percentile(self, vm : VmModel):
        """Generate two random values representing an average and a percentile included in profile bounds

        Parameters
        ----------
        vm : VmModel
            VM to take into account

        Returns
        -------
        average : int
            randomly chosen average cpu value
        percentile : int
            randomly chosen percentile cpu value
        """
        avg_min, avg_max = self.profiles[vm.get_profile()].get_average_bounds()
        per_min, per_max = self.profiles[vm.get_profile()].get_percentile_bounds()
        vm.set_avg(random.randrange(math.ceil(avg_min), math.floor(avg_max)))
        vm.set_per(random.randrange(max([math.ceil(vm.get_avg()), math.ceil(per_min)]), math.floor(per_max))) # percentile is forced to be higher than avg
        return vm.get_avg(), vm.get_per()

    def __get_random_value_in(self, distribution_values : list):
        """Return a randomly pick value in list

        Parameters
        ----------
        distribution_values : list
            list to consider

        Returns
        -------
        value : int
            randomly pick value
        """
        x = round(distribution_values[random.randrange(len(distribution_values))])
        if x> 100: x=100
        if x< 1: x=1
        return x
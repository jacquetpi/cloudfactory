from cloudfactory.vmmodel import *
import numpy as np
import random

class VmUsageBuilder(object):
    """
    A class used to attribute VM usage based on their profile
    ...

    Attributes
    ----------
    profile : dict
        UsageProfile object dict
    number_of_slices_per_scope : int
        number of slices (virtual hours) per scope (virtual days)
    number_of_scope : int
        number of scope (virtual days)

    Public Methods
    -------
    build_and_set_usage_for_VM
        set for given VM its usage (list of CPU target values)
    """

    def __init__(self, profiles : dict, number_of_slices_per_scope : int, number_of_scope : int):
        self.profiles = profiles
        self.number_of_slices_per_scope=number_of_slices_per_scope
        self.number_of_scope=number_of_scope

    def build_and_set_usage_for_VM(self, vm : VmModel, postponed_scope_start : int):
        """build a coherent (based on vm attributes) usage in the form of a list of cpu usage.
        List is set as a new attribute of VM
        /!\ VM attributes related to profile usage must be fully initialised

        Parameters
        ----------
        vm : VmModel
            VM to be updated
        """
        print("TODO : consider postponed_scope_start")
        # Build phase
        if(vm.is_periodic()):
            cpu_target_list = self.__generate_periodic_workload(vm=vm)
        else:
            cpu_target_list = self.__generate_nonperiodic_workload(vm=vm)
        # Set phase
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
        for j in range(self.number_of_slices_per_scope):
            value_per_slice.append(self.__get_random_value_in(gaussian))
            
        cpu_target = list()
        for i in range(self.number_of_scope):
            for j in range(self.number_of_slices_per_scope):
                cpu_target.append(value_per_slice[j])
                if vm.is_ended(self.number_of_slices_per_scope):
                    break
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
        for i in range(self.number_of_scope):
            for j in range(self.number_of_slices_per_scope):
                cpu_target.append(self.__get_random_value_in(gaussian))
                if vm.is_ended(self.number_of_slices_per_scope):
                    break
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
        return self.__generate_gaussian_distribution_from_avg(workload_cpu_avg, workload_cpu_per)

    def __generate_gaussian_distribution_from_avg(self, workload_avg : int, workload_95th : int):
        """Generate a gaussian distribution matching vm model specifications

        Parameters
        ----------
        workload_avg : int
            average value for gaussian distribution
        workload_95th : int
            percentile value for gaussian distribution

        Returns
        -------
        x : list
            list of cpu usage value following a gaussian distribution
        """
        mu, sigma = workload_avg, workload_95th
        while True:
            s = np.random.normal(mu, sigma, 1000)
            x = [abs(item) for item in s]
            if (np.percentile(x,95)<=workload_95th):
                break
            sigma-=1
            if(sigma<=1):
                print("we should not be here")
                s = np.random.normal(mu, sigma, 100)
                break
        return x

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
        avg_min, avg_max = self.profile[vm.get_profile()].get_average_bounds()
        per_min, per_max = self.profile[vm.get_profile()].get_percentile_bounds()
        return random.randrange(avg_min, avg_max), random.randrange(per_min, per_max)

    def __get_random_value_in(self, distribution_values : list):
        """Return a randomly pick value in lis

        Parameters
        ----------
        distribution_values : list
            list to consider

        Returns
        -------
        value : int
            randomly pick value
        """
        return round(distribution_values[random.randrange(len(distribution_values))])
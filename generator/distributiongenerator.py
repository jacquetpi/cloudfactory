"""Generate statistical distributions for usage and deployment spread.

Provides Gaussian (from avg/percentile) and heavy-tail (Weibull) distributions
used when building per-VM CPU usage and when spreading VM start times over slices.
"""
import numpy as np

class DistributionGenerator(object):
    """
    A class used to generate an statistic distribution
    ...

    Public Methods
    -------
    generate_gaussian_distribution_from_avg(workload_avg, workload_95th):
        Generate a gaussian distribution
    generate_heavy_tail_gaussian_for_deployments(number_of_vms, number_of_values):
        Generate an heavy tail distribution
    """

    def generate_gaussian_distribution_from_avg(self, workload_avg : int, workload_95th : int):
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
        if mu<=0: mu=1
        while True:
            s = np.random.normal(mu, sigma, 1000)
            x = [abs(item) for item in s]
            if (np.percentile(x,95)<=workload_95th):
                break
            sigma-=0.25
            if(sigma<=0):
                sigma=1
                s = np.random.normal(mu, sigma, 100)
                break
        return x

    def generate_heavy_tail_gaussian_for_deployments(self, number_of_vms: int, number_of_values : int, weibull_form : float = 1.):
        """ Generate an heavy tail gaussian to spread a certain number of VMs through a number of deployments (in our context, slices of a scope)

        Parameters
        ----------
        number_of_vms : int
            Number of VMs to be deployed
        number_of_values : int
            Spread number of VMs through number_of_values
        weibull_form : float
            numpy internal parameter

        Return
        ----------
        modified_list : list
            The heavy_tail distribution in a list form
        """
        max_burst = number_of_vms
        normalised_list = np.random.weibull(weibull_form, number_of_values)
        max = np.max(normalised_list) 

        while True:
            # Apply correct burst
            max_ratio = max_burst/max
            f = lambda x: x*max_ratio
            modified_list = f(normalised_list)
            modified_list = np.around(modified_list)
            # Control obtained list
            sum = np.sum(modified_list)
            if sum < (number_of_vms*0.9):
                max_burst = max_burst*1.1
                continue
            if sum > (number_of_vms*1.1):
                max_burst = max_burst*0.9
                continue
            break

        return modified_list
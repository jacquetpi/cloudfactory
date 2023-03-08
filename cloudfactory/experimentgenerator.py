from cloudfactory.distributionbuilder import DistributionBuilder
from cloudfactory.usagebuilder import UsageBuilder
from cloudfactory.workloadbuilder import WorkloadBuilder

class ExperimentGenerator(object):
    """
    A class used to generate an experiment (i.e. scripts)
    ...

    Attributes
    ----------
    distribution_builder : DistributionBuilder
        DistributionBuilder object used to generate VM size and usage intensity distribution
    usage_builder : WorkloadBuilder
        WorkloadBuilder object used to generate workload
    workload_builder : WorkloadBuilder
        WorkloadBuilder object used to generate workload

    Public Methods
    -------
    gen(**kwargs):
        Generate experiment related scripts
    """

    def __init__(self, **kwargs):
        required_attributes = ["distribution_builder", "usage_builder", "workload_builder"]
        for required_attribute in required_attributes:
            if required_attribute not in kwargs: raise ValueError("Missing required attributes", required_attributes)
        self.distribution_builder=kwargs["distribution_builder"]
        self.usage_builder=kwargs["usage_builder"]
        self.workload_builder=kwargs["workload_builder"]

        slice_duration = kwargs["slice_duration"] if "slice_duration" in kwargs else 3600 # default to 1h
        scope_duration = kwargs["scope_duration"] if "scope_duration" in kwargs else 86400 # default to 24h
        number_of_slices_per_scope= slice_duration / scope_duration
        number_of_scope = kwargs["number_of_scope"] if "number_of_scope" in kwargs else 12 # default to 12

    def gen(self, **kwargs):
        """Generate experiment related scripts
            
        cpu : int
            allocated cpu objective at initialisation (if specified, mem must be too)
        mem : int
            allocated mem (GB) objective at initialisation (if specified, cpu must be too)
        vm_number : int
            alternative to (cpu,mem) objective at initialisation. We target a specific number of VMs

        Raises
        ------
        ValueError
            If (cpu,mem) and vm_number are not specified (one of the two must be)
        """
        # Configuration on first round based on vm number or cpu/mem objective
        if ("cpu" in kwargs) and ("mem" in kwargs):
            initial_vm_list = self.distribution_builder.generate_set_from_config(kwargs["cpu"], kwargs["mem"])
        elif ("vm_number" in kwargs):
            initial_vm_list = self.distribution_builder.generate_set_from_vm_number(kwargs["vm_number"])
        else:
            raise ValueError("You must specified either [cpu and mem] or [vm_number] objective")

        self.usage_builder.attribute_usage_to_vm_list(initial_vm_list)
        self.workload_builder.generate_workload_for_vm_list(initial_vm_list)

            
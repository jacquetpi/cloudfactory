from generator.distributionbuilder import DistributionBuilder
from generator.usagebuilder import UsageBuilder
from generator.workloadbuilder import WorkloadBuilder
from generator.exporter.exporterbash import ExporterBash
from generator.exporter.exportercloudsimplus import ExporterCloudSimPlus
from generator.exporter.exportercbtool import ExporterCBTool

class ExperimentGenerator(object):
    """
    Generates an experiment: a set of VMs with distribution, usage profiles, and workload commands.

    Attributes
    ----------
    distribution_builder : DistributionBuilder
        Used to generate VM flavors (CPU/mem) and VM count.
    usage_builder : UsageBuilder
        Used to assign usage profiles and CPU usage over time to VMs.
    workload_builder : WorkloadBuilder
        Used to assign workload types and generate per-VM workload commands.

    Public Methods
    -------
    gen(**kwargs)
        Generate the list of VmModel for the experiment.
    write(output_type, vm_list, slice_duration)
        Export the VM list to bash, cloudsimplus, or cbtool format.
    """

    def __init__(self, **kwargs):
        required_attributes = ["distribution_builder", "usage_builder", "workload_builder"]
        for required_attribute in required_attributes:
            if required_attribute not in kwargs: raise ValueError("Missing required attributes", required_attribute, "in", required_attributes)
        self.distribution_builder=kwargs["distribution_builder"]
        self.usage_builder=kwargs["usage_builder"]
        self.workload_builder=kwargs["workload_builder"]

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
        print("Building initial distribution")
        if ("cpu" in kwargs) and ("mem" in kwargs):
            vm_list = self.distribution_builder.generate_set_from_config(kwargs["cpu"], kwargs["mem"])
        elif ("vm_number" in kwargs):
            vm_list = self.distribution_builder.generate_set_from_vm_number(kwargs["vm_number"])
        else:
            raise ValueError("You must specified either [cpu and mem] or [vm_number] objective")

        self.usage_builder.attribute_usage_to_vm_list(vm_list)
        self.workload_builder.attribute_workload_commands_to_vm_list(vm_list)

        additional_vm_count = self.usage_builder.get_overall_count_of_vm_to_be_created()
        if additional_vm_count <= 0: 
            return vm_list

        for additional_scope in range(1, kwargs["number_of_scope"]):
            print("Building scope", additional_scope)
            additional_vm = self.distribution_builder.generate_set_from_vm_number(additional_vm_count)
            self.usage_builder.attribute_usage_to_vm_list(additional_vm, postponed_scope_start=additional_scope)
            self.workload_builder.attribute_workload_commands_to_vm_list(additional_vm)
            vm_list.extend(additional_vm)

        return vm_list

    def write(self, output_type : str, vm_list : list, slice_duration : int):
        """Export vm_list to the given output format (bash, cloudsimplus, cbtool).
        Writes files in the current working directory. Raises ValueError for invalid output_type."""
        if output_type == "bash":
            exporter = ExporterBash(self.workload_builder.get_context("folder"))
        elif output_type == "cloudsimplus":
            exporter = ExporterCloudSimPlus("static/cloudsimplus.skeleton")
        elif output_type == "cbtool":
            exporter = ExporterCBTool("static/cbtool.skeleton")
        else:
            raise ValueError("Invalid output type")
        exporter.write(vm_list, slice_duration)
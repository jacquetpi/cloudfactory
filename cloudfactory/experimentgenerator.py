from cloudfactory.distributionbuilder import DistributionBuilder
from cloudfactory.usagebuilder import UsageBuilder
from cloudfactory.workloadbuilder import WorkloadBuilder
from cloudfactory.vmmodel import *

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
    tool_folder : str
        bash tool location

    Public Methods
    -------
    gen(**kwargs):
        Generate experiment related scripts
    """

    def __init__(self, **kwargs):
        required_attributes = ["distribution_builder", "usage_builder", "workload_builder"]
        for required_attribute in required_attributes:
            if required_attribute not in kwargs: raise ValueError("Missing required attributes", required_attribute, "in", required_attributes)
        self.distribution_builder=kwargs["distribution_builder"]
        self.usage_builder=kwargs["usage_builder"]
        self.workload_builder=kwargs["workload_builder"]
        self.tool_folder = self.workload_builder.get_context("folder") + "/"

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
            self.usage_builder.attribute_usage_to_vm_list(additional_vm)
            self.workload_builder.attribute_workload_commands_to_vm_list(additional_vm)
            vm_list.extend(additional_vm)

        return vm_list

    def write_setup(self, vm_list : list):
        """Generate a bash script to setup workload. Will be written at programm call location
        vm_list : list
            list of VM
        slice_duration : int
            context data, used for postponed command
        """
        count=0
        with open('setup.sh', 'w') as f:
            f.write("#!/bin/bash\n")
            count=0
            for vm in vm_list:
                f.write("( " + vm.get_setup_command(self.tool_folder) + vm.get_shutdown_command(self.tool_folder) + ") &")
                f.write('\n')
                count+=1
                if (count%10==0):
                    f.write('sleep 300\n')
            print("Setup wrote in setup.sh") 

    def write_workload_local(self, vm_list, slice_duration : int):
        """Generate a bash script to execute workload in local. Will be written at programm call location
        vm_list : list
            list of VM
        slice_duration : int
            context data, used for postponed command
        """
        with open('workload-local.sh', 'w') as f:
            f.write("#!/bin/bash\n")
            for vm in vm_list:
                f.write("( " +  self.__write_workload_line(vm, slice_duration) + ") &")
                f.write('\n')
        print("Workload wrote in workload-local.sh") 

    def write_workload_remote(self, vm_list : list, slice_duration : int):
        """Generate a bash script to execute workload remotely. Will be written at programm call location
        vm_list : list
            list of VM
        slice_duration : int
            context data, used for postponed command
        """
        count=0
        with open('workload-remote.sh', 'w') as f:
            f.write("#!/bin/bash\n")
            f.write("if (( \"$#\" != \"1\" ))\n")
            f.write("then\n")
            f.write("echo \"Missing argument : ./workload-remote.sh remoteip\"\n")
            f.write("exit -1\n")
            f.write("fi\n")
            f.write("remoteip=\"$1\"\n")
            for vm in vm_list:
                f.write("( " +  self.__write_workload_line(vm, slice_duration, remote = True) + ") &")
                f.write('\n')
            print("Workload wrote in workload-remote.sh") 

    def write_setup_remote(self, vm_list : list):
        """Generate a bash script to setup remote workload execution. Will be written at programm call location
        vm_list : list
            list of VM
        """
        with open('setup-firewall-for-remote.sh', 'w') as f:
            f.write("#!/bin/bash\n")
            f.write("sudo firewall-cmd --reload\n")
            for vm in vm_list:
                f.write(vm.get_nat_setup_command(self.tool_folder))
                f.write('\n')
            f.write("sudo firewall-cmd --direct --add-rule ipv4 nat POSTROUTING 0 -j MASQUERADE\n")
            f.write("sudo firewall-cmd --direct --add-rule ipv4 filter FORWARD 0 -d 0.0.0.0/0 -j ACCEPT\n")
        print("Remote setup wrote in setup-firewall-for-remote.sh")

    def __write_workload_line(self, vm : VmModel, slice_duration : int, remote : bool = False):
        """Return a string containing bash instruction to execute workload for given VM
        vm : VmModel
            Vm considered
        slice_duration : int
            context data, used for postponed command
        remote : bool
            Remotely execute workload or not (change vm identifier)

        Return
        ------
        command : str
            bash command as string
        """
        return vm.get_postponed_command(slice_duration=slice_duration) + vm.get_start_command(self.tool_folder) + vm.get_commands_as_str(remote=remote) + vm.get_shutdown_command(self.tool_folder)
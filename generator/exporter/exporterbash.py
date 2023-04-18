from generator.vmmodel import *

class ExporterBash(object):
    """
    A class used to translate a workload to bash scripts
    ...

    Attributes
    ----------
    tool_folder : str
        Directory where generic bash scripts can be found

    Public Methods
    -------
    write(vm_list : list, slice_duration : int):
        Generate experiment related bash scripts
    """
    
    def __init__(self, tool_folder : str):
        self.tool_folder = tool_folder
        if not self.tool_folder.endswith("/"):
            self.tool_folder+= "/"

    def write(self, vm_list : list, slice_duration : int):
        """Generate experiment related bash scripts
        vm_list : list
            list of VM
        slice_duration : int
            context data, used for postponed command   
        """
        self.__write_setup(vm_list)
        self.__write_setup_remote(vm_list)
        self.__write_workload_local(vm_list, slice_duration)
        self.__write_workload_remote(vm_list, slice_duration)

    def __write_setup(self, vm_list : list):
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
                f.write("( " + self.__vm_setup_command(vm, self.tool_folder) + self.__vm_shutdown_command(vm, self.tool_folder) + ") &")
                f.write('\n')
                count+=1
                if (count%10==0):
                    f.write('sleep 300\n')
            print("Setup wrote in setup.sh") 

    def __write_workload_local(self, vm_list, slice_duration : int):
        """Generate a bash script to execute workload in local. Will be written at programm call location
        vm_list : list
            list of VM
        slice_duration : int
            context data, used for postponed command
        """
        with open('workload-local.sh', 'w') as f:
            f.write("#!/bin/bash\n")
            for vm in vm_list:
                f.write("( " +  self.__get_workload_line(vm, slice_duration) + ") &")
                f.write('\n')
        print("Workload wrote in workload-local.sh") 

    def __write_workload_remote(self, vm_list : list, slice_duration : int):
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
                f.write("( " +  self.__get_workload_line(vm, slice_duration, remote = True) + ") &")
                f.write('\n')
            print("Workload wrote in workload-remote.sh") 

    def __write_setup_remote(self, vm_list : list):
        """Generate a bash script to setup remote workload execution. Will be written at programm call location
        vm_list : list
            list of VM
        """
        with open('setup-firewall-for-remote.sh', 'w') as f:
            f.write("#!/bin/bash\n")
            f.write("sudo firewall-cmd --reload\n")
            for vm in vm_list:
                f.write(self.__vm_nat_setup_command(vm, self.tool_folder))
                f.write('\n')
            f.write("sudo firewall-cmd --direct --add-rule ipv4 nat POSTROUTING 0 -j MASQUERADE\n")
            f.write("sudo firewall-cmd --direct --add-rule ipv4 filter FORWARD 0 -d 0.0.0.0/0 -j ACCEPT\n")
        print("Remote setup wrote in setup-firewall-for-remote.sh")

    def __get_workload_line(self, vm : VmModel, slice_duration : int, remote : bool = False):
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
        return self.__vm_postponed_command(vm, slice_duration=slice_duration) + self.__vm_start_command(vm, self.tool_folder) + self.__vm_commands_as_str(vm, remote=remote) + self.__vm_shutdown_command(vm, self.tool_folder)

    def __vm_setup_command(self, vm : VmModel, folder : str):
        return folder + "setupvm.sh " + vm.get_name() + " " + str(vm.get_cpu()) + " " + str(round(vm.get_mem()*1024)) + " " + vm.get_workload() + " ; "

    def __vm_nat_setup_command(self, vm : VmModel, folder : str):
        return folder + "setupvmnat.sh " + vm.get_name() + " " + vm.get_workload() + " " + str(self.__vm_host_port(vm)) + " ; "

    def __vm_destroy_command(self, vm : VmModel, folder : str):
        return folder + "destroyvm.sh " + vm.get_name() + " ; "

    def __vm_start_command(self, vm : VmModel, folder : str):
        return folder + "startvm.sh " + vm.get_name() + " " +  vm.get_workload() + " ; "

    def __vm_shutdown_command(self,  vm : VmModel, folder : str):
        return folder + "shutdownvm.sh " + vm.get_name() + " ; "

    def __vm_nat_destroy_command(self, vm : VmModel, folder : str):
        return folder + "destroyvmnat.sh " + vm.get_name() + " ; "

    def __vm_postponed_command(self, vm : VmModel, slice_duration : int):
        postponed_slice = vm.get_postponed_start()
        if postponed_slice<=0: return ""
        duration = postponed_slice*slice_duration
        return "sleep " + str(duration) + " ; "

    def __vm_commands_as_str(self, vm : VmModel, remote : bool = False):
        gen_str = ""
        identifier = vm.get_name()
        if remote:
            identifier = "${remoteip}:" + str(self.__vm_host_port(vm))
        for command in vm.get_commands_list():
            gen_str += command.replace("§name", identifier) + " ; "
        return gen_str

    def __vm_host_port(self, vm : VmModel):
        return 11000 + int(vm.get_id()) # to avoid common ports
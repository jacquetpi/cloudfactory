"""Export CloudFactory VM workload to CloudSim Plus.

Writes CloudFactoryGeneratedWorkload.java (from skeleton), vms.properties,
and models.properties for use with the CloudSim Plus simulator.
"""
from generator.vmmodel import *

class ExporterCloudSimPlus(object):
    """
    Exports a VM workload to CloudSim Plus Java and properties files.

    Attributes
    ----------
    skeleton : str
        Contents of the Java CloudSim program skeleton (loaded from file at init).

    Public Methods
    -------
    write(vm_list, slice_duration)
        Write Java source and properties files to the current directory.
    """
    
    def __init__(self, skeleton_location : str):
        with open(skeleton_location, 'r') as file:
            self.skeleton = file.read()
    
    def write(self, vm_list : list, slice_duration : int):
        """Write CloudSim Plus Java workload and properties files.

        Parameters
        ----------
        vm_list : list
            List of VmModel to export.
        slice_duration : int
            Duration of one slice in seconds for the experiment.
        """
        with open('CloudFactoryGeneratedWorkload.java', 'w') as f:
            f.write(self.skeleton)
        with open('vms.properties', 'w') as f:
            f.write(self.__get_setup(vm_list, slice_duration))
        with open('models.properties', 'w') as f:
            f.write(self.__get_usage_model(vm_list, slice_duration))
        print("Workload wrote in CloudFactoryGeneratedWorkload.java and CloudFactoryGeneratedWorkload.properties") 

    def __get_setup(self, vm_list : list, slice_duration : int):
        """Return setup of all vm as a string of properties
        vm_list : list
            list of VM
        slice_duration : int
            Duration of a slice in given experiment

        Return
        ------
        command : str
            properties as string
        """
        properties  = ""
        for vm in vm_list:
            vm_name =  "vm" + str(vm.get_id())
            properties+= vm_name + "=" + self.__get_setup_for_vm(vm, slice_duration) + "," + self.__get_workload_for_vm(vm, slice_duration) + "\n"

        return properties
    
    def __get_setup_for_vm(self, vm : VmModel, slice_duration : int):
        """Return setup of a single vm as a string of properties
        vm : VmModel
            vm to consider

        Return
        ------
        command : str
            properties as string     
        """
        mem_mb = round(vm.get_mem() * 1024)
        based_mips = 1000
        vm_mips = max([int(based_mips*(max(vm.get_usage())/100)) , 1])
        bandwith = 1000
        size_mb = 10000

        return "vmid:" + str(vm.get_id()) + "," +\
            "vmmips:" + str(vm_mips) + "," +\
            "vmcpu:" + str(vm.get_cpu()) + "," +\
            "vmram:" + str(mem_mb) + "," +\
            "vmbw:" + str(bandwith) + "," +\
            "vmsize:" +  str(size_mb) + "," +\
            "vmsubmission:" + str(int(vm.get_postponed_start()*slice_duration))

    def __get_workload_for_vm(self, vm : VmModel, slice_duration : int):
        """Return workload of a single vm as a string of properties
        vm : VmModel
            vm to consider
        slice_duration : int
            Duration of a slice in given experiment

        Return
        ------
        command : str
            data as properties string     
        """
        lifetime_s = self.__compute_lifetime_for_vm(vm, slice_duration)
        #end_time_s = (vm.get_postponed_start()*slice_duration) + lifetime_s
        based_mips = 1000
        filesize = 300
        outputsize = 300
        vm_name = "vm" + str(vm.get_id())
        utilisation_model = vm_name + "_model"

        return "cloudletid:" + str(vm.get_id()) + "," +\
            "cloudletmips:" + str(int(lifetime_s*based_mips)) + "," +\
            "cloudletcpu:" + str(vm.get_cpu()) + "," +\
            "cloudletfilesize:" + str(filesize) + "," +\
            "cloudletoutputsize:" + str(outputsize) + "," +\
            "cloudletmodel:" + utilisation_model + "," +\
            "cloudletvm:" + vm_name + "," +\
            "cloudletlifetime:" + str(lifetime_s)

    def __compute_lifetime_for_vm(self, vm : VmModel, slice_duration):
        """Compute vm lifetime from its timesheet
        vm : vmModel
            vm to consider
        slice_duration : int
            Duration of a slice in given experiment

        Return
        ------
        value : int
            lifetime as seconds     
        """
        if vm.get_lifetime()>0:
           slice_count = vm.get_lifetime()
        else:
            slice_count = 0
            timesheet = vm.get_timesheet()
            for scope in timesheet.values():
                for slice_presence in scope:
                    if slice_presence: slice_count+=1
        return int(slice_count*slice_duration)

    def __get_usage_model(self, vm_list : list, slice_duration : int):
        """Return usage models and associated properties of all vm as a string of java methods
        vm_list : list
            list of VM
        slice_duration : int
            Duration of a slice in given experiment

        Return
        ------
        properties : str
            model properties data as string     
        """
        properties = ""
        for vm in vm_list:
            model_name =  "vm" + str(vm.get_id()) + "_model"
            properties += model_name  + "=" + self.__get_usage_model_for_vm(vm, slice_duration) + "\n"
        return properties

    def __get_usage_model_for_vm(self, vm : VmModel, slice_duration : int):
        """Return usage model of a single vm as json string
        vm : vmModel
            vm to consider
        slice_duration : int
            Duration of a slice in given experiment

        Return
        ------
        command : str
            json as string     
        """
        # We first associate generated usage level to the time at which they should be used
        # Generated dict must be read as following : For a given time, usage level to use should be the one associated to the first key where time<key
        timesheet = vm.get_timesheet()
        target_values = vm.get_usage()
        target_index = 0
        target_associated_to_lower = dict()
        slice_key = vm.get_postponed_start()*slice_duration
        for scope in timesheet.values():
            for slice_presence in scope:
                slice_key+= slice_duration
                if not slice_presence: continue
                target_associated_to_lower[slice_key] = target_values[target_index]
                target_index+=1
        # Convert to string
        return ''.join(str(time) + ":" + str(target_associated_to_lower[time]) + "," for time in target_associated_to_lower)[:-1]
"""Export CloudFactory VM workload to CBTOOL scenario.

Writes a cloudfactory.cbtool scenario file that can be run with CBTOOL
(cbtool/cb --trace=cloudfactory.cbtool) for simulation or cloud deployment.
"""
from generator.vmmodel import *

class ExporterCBTool(object):
    """
    Exports a VM workload to a CBTOOL scenario script.

    Attributes
    ----------
    skeleton : str
        CBTOOL scenario template (loaded from file at init); contains §commands§ placeholder.
    default_cbtool_config : dict
        Maps CPU count to allowed memory (MB) options for CBTOOL VM sizing.

    Public Methods
    -------
    write(vm_list, slice_duration)
        Write cloudfactory.cbtool to the current directory.
    """
    
    def __init__(self, skeleton_location : str):
        with open(skeleton_location, 'r') as file:
            self.skeleton = file.read()
        
        self.default_cbtool_config = {
            1:[192,512,1024,2048],
            2:[2048,4096],
            4:[2048,8192],
            8:[4096,16384],
            16:[16384],
            24:[32768]}

    def write(self, vm_list : list, slice_duration : int):
        """Write CBTOOL scenario file for the given VM list.

        Parameters
        ----------
        vm_list : list
            List of VmModel to export.
        slice_duration : int
            Duration of one slice in seconds; used for load_duration and waitfor.
        """
        cbtool_code = self.skeleton.replace("§commands§", self.__get_commands(vm_list, slice_duration))
        with open('cloudfactory.cbtool', 'w') as f:
            f.write(cbtool_code)
        print("Scenario wrote in cloudfactory.cbtool")

    def __get_commands(self, vm_list : list, slice_duration : int):
        """Return CBTOOL scenario of all vm as a string
        vm_list : list
            list of VM
        slice_duration : int
            Duration of a slice in given experiment

        Return
        ------
        command : str
            CBTOOL scenario as string     
        """
        scenario = ""
        overall_timesheet = vm_list[0].get_timesheet() # We ignore specific slice values, we only want timesheet structure
        track_cbtool_names = {'_index':0} # use to follow CB tool virtual applications names (ai_index) 
        for scope_index, scope_values in overall_timesheet.items():
            for slice_index in range(len(scope_values)):
                scenario+= self.__get_scenario_on_specific_slice(vm_list=vm_list,
                    slice_duration=slice_duration,
                    scope_index=scope_index,
                    slice_index=slice_index,
                    tracker=track_cbtool_names)
                scenario+= "waitfor " + str(slice_duration) + "s\n"
        return scenario

    def __get_scenario_on_specific_slice(self, vm_list : list, slice_duration : int, scope_index : int, slice_index : int, tracker : dict):
        """Return CBTOOL scenario of all vm as a string on a specific slice
        vm_list : list
            list of VM
        slice_duration : int
            Duration of a slice in given experiment
        scope_index : int
            scope index
        slice_index : int
            slice index
        tracker : dict
            Dict tracking CBTOOL virtual application name associated to each VM

        Return
        ------
        command : str
            CBTOOL command as string     
        """
        scenario = ""
        for vm in vm_list:
            attendance = vm.get_timesheet()[scope_index][slice_index]
            if (attendance == True) and (self.__previous_attendance(tracker, vm) == False):
                scenario += self.__get_setup_for_vm(tracker, vm, slice_duration)
            if (attendance == False) and (self.__previous_attendance(tracker, vm) == True):
                scenario += self.__get_detach_for_vm(tracker, vm)
        return scenario

    def __previous_attendance(self, tracker : dict, vm : VmModel):
        """Return a boolean based on previous attendance of specified VM
        vm : VmModel
            vm to consider
        tracker : dict
            Dict tracking CBTOOL virtual application name associated to each VM

        Return
        ------
        attendance : bool
            True if was present, False otherwise
        """
        if str(vm.get_id()) in tracker:
            return True
        return False

    def __get_setup_for_vm(self, tracker : dict, vm : VmModel, slice_duration : int):
        """Return setup of a single vm as a string of CBTOOL commands. Update also tracker
        tracker : dict
            Dict tracking CBTOOL virtual application name associated to each VM
        vm : VmModel
            vm to consider
        slice_duration : int
            Duration of a slice in given experiment

        Return
        ------
        command : str
            CBTOOL commands as string     
        """
        tracker["_index"] += 1
        tracker[str(vm.get_id())] = "ai_" + str(tracker["_index"])

        application = self.__choose_application_for_vm(vm)
        attach_async = "" # " async"

        commands  = "rolealter " + application + " size=" + self.__get_closest_config(vm.get_cpu(), vm.get_mem()) + "\n"
        #commands += "typealter " + application + " load_level=25\n"
        commands += "typealter " + application + " load_level=uniformIXIXI" + str(vm.get_avg()) + "I" + str(vm.get_per()) + "\n"
        commands += "typealter " + application + " load_duration=" + str(slice_duration) +"\n" # change each 5mn"
        commands += "aiattach "  + application + attach_async + "\n"
        return commands

    def __get_detach_for_vm(self, tracker : dict, vm : VmModel):
        """Return detach of a single vm as a string of CBTOOL command. Update also tracker
        vm : VmModel
            vm to consider
        tracker : dict
            Dict tracking CBTOOL virtual application name associated to each VM

        Return
        ------
        command : str
            CBTOOL command as string     
        """
        command = "aidetach " + tracker[str(vm.get_id())] + "\n"
        del tracker[str(vm.get_id())]
        return command

    def __choose_application_for_vm(self,vm : VmModel):
        """Return cbtool application for a vm as a string of CBTOOL command. Update also tracker
        vm : VmModel
            vm to consider

        Return
        ------
        application : str
            application name
        """
        return "stress" # TODO: more applications

    def __get_closest_config(self, cpu : int, mem : int):
        """Given a request of cpu and memory, return the closest cbtool config
        cpu : int
            CPU requested
        mem : int
            mem requested (MB or GB)

        Return
        ------
        config : str
            cbtool config as a string            
        """
        requested_mem = mem
        if requested_mem < 192: requested_mem = requested_mem*1024
        for config_memory in self.default_cbtool_config[cpu]:
            chosen_memory = config_memory
            if requested_mem < config_memory:
                break
        cpu_as_str = str(cpu) if cpu > 10 else "0" + str(cpu)
        return cpu_as_str + "-" + str(chosen_memory)
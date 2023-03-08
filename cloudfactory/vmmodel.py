from random import randrange
from json import JSONEncoder

class VmModel(object): 
    """
    A class used to represent a VM
    ...

    Attributes
    ----------
    vm_name : str
        VM identifier, 
    cpu : int
        VM cpu amount
    mem : int
        VM mem amount
    host_port : int
        unique host port which can be used for nating

    Methods
    -------
    __load_from_yaml(yaml_file=None)
        initiate attributes from yaml config file
    """

    vm_count = 0  # Static

    def __init__(self, **kwargs):
        required_attributes = ["cpu", "mem"]
        for required_attribute in required_attributes:
            if required_attribute not in kwargs: raise ValueError("Missing required attributes", required_attributes)
        VmModel.vm_count+=1
        self.cpu = kwargs["cpu"]
        self.mem = kwargs["mem"]
        self.name = kwargs["name"] if "name" in kwargs else "vm" + str(VmModel.vm_count)
        self.host_port = kwargs["host_port"] if "host_port" in kwargs else VmModel.vm_count + 11000

    def set_lifetime(self, scope_lifetime : int):
        self.scope_lifetime = scope_lifetime # 0 is infinite

    def set_postponed_start(self, postponed_slice : int):
        self.postponed_slice = postponed_slice

    def get_postponed_command(self, slice_duration : int):
        if not hasattr(self, 'postponed_slice'):
            return ""
        duration = self.postponed_slice*slice_duration
        return "sleep " + str(duration) + " ; "

    def get_setup_command(self):
        return VmModel.TOOL_FOLDER + "setupvm.sh " + self.vm_name + " " + str(self.cpu) + " " + str(round(self.mem*1024)) + " " + self.workload + " ; "

    def get_nat_setup_command(self):
        return VmModel.TOOL_FOLDER + "setupvmnat.sh " + self.vm_name + " " + self.workload + " " + str(self.host_port) + " ; "

    def get_destroy_command(self):
        return VmModel.TOOL_FOLDER + "destroyvm.sh " + self.vm_name + " ; "

    def get_start_command(self):
        return VmModel.TOOL_FOLDER + "startvm.sh " + self.vm_name + " " + self.workload + " ; "

    def get_shutdown_command(self):
        return VmModel.TOOL_FOLDER  + "shutdownvm.sh " + self.vm_name + " ; "

    def get_nat_destroy_command(self):
        return VmModel.TOOL_FOLDER + "destroyvmnat.sh " + self.vm_name + " ; "

    def is_ended(self, number_of_slices_per_scope : int):
        if (self.scope_lifetime == 0): # Infinite lifetime
            return False

        # Initialisation
        if not hasattr(self, 'slice_lifetime_count'):
            # We compute lifetime based with a slight random factor to spread through slices VM extinction
            self.slice_lifetime_count = number_of_slices_per_scope*self.scope_lifetime
            # If VM is postponed, random factor is already integrated in its starting time
            if not hasattr(self, 'postponed_slice'):
                self.slice_lifetime_count+= randrange(0,number_of_slices_per_scope)
           
        # Update count
        self.slice_lifetime_count-=1
        return self.slice_lifetime_count<=0

    def get_host_port(self):
        return self.host_port

    def get_cpu(self):
        return self.cpu

    def get_mem(self):
        return self.mem

    def get_name(self):
        return self.name

    def get_profile(self):
        if not hasattr(self, 'profile'):
            return None
        return self.profile
    
    def set_profile(self, profile : str):
        self.profile = profile

    def set_periodicity(self, periodicity : bool):
        self.periodicity = periodicity

    def is_periodic(self):
        if not hasattr(self, 'periodicity'):
            return False
        return True

    def set_usage(self, target_usage : list):
        self.usage = target_usage

    def get_usage(self, target_usage : list): 
        return self.usage
        
class VmModelEncoder(JSONEncoder):
    def default(self, o):
        return o.__dict__  
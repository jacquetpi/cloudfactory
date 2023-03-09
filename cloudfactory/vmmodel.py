from random import randrange
from json import JSONEncoder

class VmModel(object): 
    """
    A class used to represent a VM
    ...

    Attributes (minimal)
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
    getter/setter
    """

    vm_count = 0  # Static

    def __init__(self, **kwargs):
        required_attributes = ["cpu", "mem"]
        for required_attribute in required_attributes:
            if required_attribute not in kwargs: raise ValueError("Missing required attributes", required_attribute, "in", required_attributes)
        VmModel.vm_count+=1
        self.cpu = kwargs["cpu"]
        self.mem = kwargs["mem"]
        self.name = kwargs["name"] if "name" in kwargs else "vm" + str(VmModel.vm_count)
        self.host_port = kwargs["host_port"] if "host_port" in kwargs else VmModel.vm_count + 11000

    def get_setup_command(self, folder : str):
        return folder + "setupvm.sh " + self.get_name() + " " + str(self.get_cpu()) + " " + str(round(self.get_mem()*1024)) + " " + self.get_workload() + " ; "

    def get_nat_setup_command(self, folder : str):
        return folder + "setupvmnat.sh " + self.get_name() + " " + self.get_workload() + " " + str(self.get_host_port()) + " ; "

    def get_destroy_command(self, folder : str):
        return folder + "destroyvm.sh " + self.get_name() + " ; "

    def get_start_command(self, folder : str):
        return folder +"startvm.sh " + self.get_name() + " " +  self.get_workload() + " ; "

    def get_shutdown_command(self, folder : str):
        return folder + "shutdownvm.sh " + self.get_name() + " ; "

    def get_nat_destroy_command(self, folder : str):
        return folder + "destroyvmnat.sh " + self.get_name() + " ; "

    def set_lifetime(self, slice_lifetime : int):
        self.slice_lifetime = slice_lifetime # 0 is infinite

    def get_lifetime(self):
        return self.slice_lifetime

    def set_postponed_start(self, postponed_slice : int):
        self.postponed_slice = postponed_slice

    def get_postponed_start(self):
        return self.postponed_slice

    def get_postponed_command(self, slice_duration : int):
        if not hasattr(self, 'postponed_slice') or self.postponed_slice<=0:
            return ""
        duration = self.postponed_slice*slice_duration
        return "sleep " + str(duration) + " ; "

    def set_timesheet(self, timesheet : dict):
        self.timesheet = timesheet

    def get_timesheet(self):
        return self.timesheet

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
        return self.periodicity

    def set_usage(self, target_usage : list):
        self.usage = target_usage

    def get_usage(self): 
        return self.usage

    def set_workload(self, workload : str): 
        self.workload = workload
        
    def get_workload(self): 
        return self.workload

    def set_commands_list(self, commands_list : list): 
        self.commands_list = commands_list

    def get_commands_as_str(self, remote : bool = False):
        gen_str = ""
        identifier = self.get_name()
        if remote:
            identifier = "${remoteip}:" + str(self.get_host_port())
        for command in self.commands_list:
            gen_str += command.replace("§name", identifier) + " ; "
        return gen_str

class VmModelEncoder(JSONEncoder):
    def default(self, o):
        return o.__dict__  
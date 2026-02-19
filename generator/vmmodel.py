"""VM model: core data structure for a single VM in a generated workload.

VmModel holds flavor (cpu, mem), identity (id, name), lifecycle (lifetime,
postponed_start, timesheet), usage profile and generated usage list, workload
type, and generated commands_list. Used by all builders and exporters.
"""
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
        for attribute, value in kwargs.items():
            setattr(self, attribute, value)
        if not hasattr(self, "name"): self.name = "vm" + str(VmModel.vm_count)
        if not hasattr(self, "id"): self.id = VmModel.vm_count
        VmModel.vm_count+=1

    # Getter on required attributes
    def get_id(self):
        return self.id

    def get_cpu(self):
        return self.cpu

    def get_mem(self):
        return self.mem

    def get_name(self):
        return self.name

    # Getter on optional attributes
    def set_lifetime(self, slice_lifetime : int):
        self.slice_lifetime = slice_lifetime # 0 is infinite

    def get_lifetime(self):
        if not hasattr(self, 'slice_lifetime'): return 0
        return self.slice_lifetime

    def set_postponed_start(self, slice_postponed : int):
        self.slice_postponed = slice_postponed

    def get_postponed_start(self):
        if not hasattr(self, 'slice_postponed'): return 0
        return self.slice_postponed

    def set_timesheet(self, timesheet : dict):
        self.timesheet = timesheet

    def get_timesheet(self):
        if not hasattr(self, 'timesheet'): return dict()
        return self.timesheet
    
    def set_profile(self, profile : str):
        self.profile = profile

    def set_avg(self, avg : int):
        self.avg = avg

    def get_avg(self): 
        if not hasattr(self, 'avg'): return None
        return self.avg

    def set_per(self, per : int):
        self.per = per

    def get_per(self): 
        if not hasattr(self, 'per'): return None
        return self.per

    def get_profile(self):
        if not hasattr(self, 'profile'): return None
        return self.profile

    def set_periodicity(self, periodicity : bool):
        self.periodicity = periodicity

    def is_periodic(self):
        if not hasattr(self, 'periodicity'): return False
        return self.periodicity

    def set_usage(self, target_usage : list):
        self.usage = target_usage

    def get_usage(self): 
        if not hasattr(self, 'usage'): return list()
        return self.usage

    def set_workload(self, workload : str): 
        self.workload = workload
        
    def get_workload(self): 
        if not hasattr(self, 'workload'): return None
        return self.workload

    def set_commands_list(self, commands_list : list): 
        self.commands_list = commands_list

    def get_commands_list(self):
        if not hasattr(self, 'commands_list'): return list()
        return self.commands_list

class VmModelEncoder(JSONEncoder):
    """JSON encoder for VmModel: serializes as the VM's __dict__ for export/reload."""

    def default(self, o):
        if type(o) is not VmModel:
            return 
        return o.__dict__  
import yaml 

class WorkloadBuilder(object):
    """
    A class used to generate workload based on scenario, requested temporality and usage pattern
    ...

    Attributes
    ----------
    acronyms : dict
        value to be replaced in command generation
    vm_workloads : dict
        VM workloads description

    Methods
    -------
    toto
        toto
    """
    def __init__(self, **kwargs):
        required_attributes = ["yaml_file"]
        for required_attribute in required_attributes:
            if required_attribute not in kwargs: raise ValueError("Missing required attributes", required_attributes)
        self.__load_from_yaml(kwargs["yaml_file"])

    def __load_from_yaml(self, yaml_file : str):
        with open(yaml_file, 'r') as file:
            yaml_as_dict = yaml.full_load(file)
        self.acronyms = yaml_as_dict["acronyms"] if "acronyms" in yaml_as_dict else dict()
        self.acronyms = yaml_as_dict["vm_workloads"]
    
    def generate_workload_for_vm_list(self, vm_list : list):
        """Generate workload for each VM
        /!\ VM must have a usage previously attributed

        Parameters
        ----------
        vm_list : list
            list of VMs : VM object will be updated with workload
        """

    def attribute_workload_for_vm_list(self, vm_list : list):
        """Attribute given workloads to each VM
        /!\ VM must have a usage previously attributed

        Parameters
        ----------
        vm_list : list
            list of VMs : VM object will be updated with workload
        """
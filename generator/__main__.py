import getopt, sys, json
from generator.distributionbuilder import DistributionBuilder
from generator.usagebuilder import UsageBuilder
from generator.workloadbuilder import WorkloadBuilder
from generator.experimentgenerator import ExperimentGenerator
from generator.vmmodel import *

# Default values
yaml_file_distrib_default = "examples-scenario/scenario-vm-distribution-azure2017.yml"
yaml_file_usage_default   = "examples-scenario/scenario-vm-usage-azure2017.yml"
yaml_file_workload_default = "examples-workload/scenario-vm-workload.yml"
temporality_slice_duration_default = 3600 # 1h
temporality_scope_duration_default = 86400 # 24h
temporality_scope_number_default = 12
valid_output = ['bash', 'cloudsimplus', 'cbtool']

def print_usage():
    print("")
    print("[CloudFactory usage]")
    print("python3 -m generator [options]")
    print("")
    print("Config options:")
    print("[--distribution={scenario-distrib.yml}] : distribution scenario (as yaml file) location. Default :", yaml_file_distrib_default)
    print("[--usage={scenario-usage.yml}]          : usage scenario (as yaml file) location. Default :", yaml_file_usage_default)
    print("[--workload={workload.yml}]             : workload (as yaml file) location. Default :", yaml_file_workload_default)
    print("Generating set options:")
    print("[--cpu={cores}] [--mem={gb}] : initialize a set of VM based on requested usage (as cpu cores and mem gigabytes provisioned quantities)")
    print("[--vm={number_of_vm}]        : initialize a set of requested amount of VM")
    print("[--load={vm_list.json}]      : alternatively, load a previously generated set of VM (using --export option)")
    print("Temporality option:")
    print("[--temporality={slice,scope,iteration}] :  virtual hour duration (seconds), virtual day duration (seconds), number of experiment vdays. Default:", 
        str("--temporality=" + str(temporality_slice_duration_default) + "," + str(temporality_scope_duration_default) + "," + str(temporality_scope_number_default)))
    print("Output options:")
    print("[--output={bash/cloudsim/cbtool}] : output format list, separated by comma (can be single)")
    print("[--export={vm_list.json}]         : if specified, export generated set of VM to the location (for reproductibility purposes)")
    print("")
    print(">Specific examples : To generate a bash script from a CPU/mem objective :")
    print("python3 -m generator [--cpu={used_cores}] [--mem={used_gb}] --output=bash [--temporality={slice,scope,iteration}]")
    print(">Specific examples : To generate a bash script from a vm number objective :")
    print("python3 -m generator [--vm={vm_number}] --output=bash --temporality={slice,scope,iteration}]")
    sys.exit(0)

def manage_temporality_args(argument : str):
    values = argument.split(',')
    if len(values) != 3:
        print("Invalid length on temporality arguments. Refer to format")
        print_usage()
    slice = int(values[0])
    scope = int(values[1])
    number = int(values[2])
    if slice > scope:
        raise ValueError("Model scope must be greater than slice scope")
    if scope % slice !=0:
        raise ValueError("Model scope must be a slice multiple")
    return slice, scope, number

def manage_output_args(argument : str):
    output_selected = list()
    for format in argument.split(','):
        if format not in valid_output:
            print("Invalid format selected", format, "expected ones :", valid_output)
            raise ValueError("Invalid output argument")
        output_selected.append(format)
    return output_selected

def manage_vm_load_arg(argument : str):
    vm_list = list()
    with open(argument, 'r') as f:
        raw_list = json.load(f)
        for raw_vm in raw_list:
            vm_list.append(VmModel(**raw_vm))
    return vm_list

if __name__ == '__main__':

    short_options = "hd:u:w:c:m:v:l:t:o:e:"
    long_options = ["help", "distribution=", "usage=", "workload=", 'cpu=', 'mem=', 'vm=', 'load=', 'temporality=', 'output=', 'export=']

    #Load default options values
    yaml_file_distrib = yaml_file_distrib_default
    yaml_file_usage   = yaml_file_usage_default
    yaml_file_workload = yaml_file_workload_default
    init_cpu  = None
    init_mem  = None
    init_vm   = None
    vm_list   = list()
    temporality_slice_duration = temporality_slice_duration_default
    temporality_scope_duration = temporality_scope_duration_default
    temporality_scope_number = temporality_scope_number_default
    temporality_slices_per_scope= int(temporality_scope_duration / temporality_slice_duration)
    output_format = list()
    output_export = None

    # Arguments management
    try:
        arguments, values = getopt.getopt(sys.argv[1:], short_options, long_options)
    except getopt.error as err:
        print(str(err))
        print_usage()
    for current_argument, current_value in arguments:
        if current_argument in ('-h', '--help'):
            print_usage()
        elif current_argument in('-d', '--distribution'):
            yaml_file_distrib = current_value
        elif current_argument in('-u', '--usage'):
            yaml_file_usage   = current_value
        elif current_argument in('-w', '--workload'):
            yaml_file_workload = current_value
        elif current_argument in('-cpu', '--cpu'):
            init_cpu = int(current_value)
        elif current_argument in('-mem', '--mem'):
            init_mem = int(current_value)
        elif current_argument in('-v', '--vm'):   
            init_vm = int(current_value)
        elif current_argument in('-l', '--load'):   
            vm_list = manage_vm_load_arg(current_value)
        elif current_argument in('-o', '--output'):
            output_format = manage_output_args(current_value)
        elif current_argument in('-e', '--export'):
            output_export = current_value
        elif current_argument in('-t', '--temporality'):
            temporality_slice_duration, temporality_scope_duration, temporality_scope_number = manage_temporality_args(current_value)
            temporality_slices_per_scope= int(temporality_scope_duration / temporality_slice_duration)
        else:
            print_usage()
            
    # Entrypoint
    try:

        # Initialization
        distribution_builder = DistributionBuilder(yaml_file=yaml_file_distrib)
        usage_builder = UsageBuilder(yaml_file=yaml_file_usage, slices_per_scope=temporality_slices_per_scope, number_of_scope=temporality_scope_number)
        workload_builder = WorkloadBuilder(yaml_file=yaml_file_workload, slice_duration=temporality_slice_duration)
        generator = ExperimentGenerator(distribution_builder=distribution_builder, usage_builder=usage_builder, workload_builder=workload_builder)

        # Generation
        if not vm_list:
            if (init_cpu is not None) and (init_mem is not None) :
                vm_list = generator.gen(cpu=init_cpu, mem=init_mem, number_of_scope=temporality_scope_number)
            elif (init_vm is not None):
                vm_list = generator.gen(vm_number=init_vm, number_of_scope=temporality_scope_number)
            else:
                print("Warning, no set of VM specified")
                print_usage()

        # Output
        if vm_list:
            for format in output_format:
                generator.write(output_type=format, vm_list=vm_list, slice_duration=temporality_slice_duration)
            if output_export is not None:
                with open(output_export, 'w') as f:
                    for vm in vm_list:
                        if not hasattr(vm, 'cpu'): print(vm, type(vm))
                    f.write(json.dumps(vm_list, cls=VmModelEncoder))
                    print("CloudFactory VM workload exported as json in", output_export)

    except KeyboardInterrupt:
        print("Program interrupted")

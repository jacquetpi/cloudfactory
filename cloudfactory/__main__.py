import getopt, sys
from cloudfactory.distributionbuilder import DistributionBuilder
from cloudfactory.usagebuilder import UsageBuilder
from cloudfactory.workloadbuilder import WorkloadBuilder
from cloudfactory.experimentgenerator import ExperimentGenerator

def print_usage():
    print(">To launch from a CPU/mem objective : ")
    print("python3 -m cloudfactory [--cpu={cores}] [--mem={gb}] [--temporality={slice,scope,iteration}]")
    print(">To launch from a vm number objective : ")
    print("python3 -m cloudfactory [--vm={vm_number}] [--temporality={slice,scope,iteration}]")   
    print(">All options:")
    print("python3 -m cloudfactory [--cpu={cores}] [--mem={gb}] [--vm={vm_number}] [--temporality={slice,scope,iteration}] [--specification] [--load={json_file}]")

if __name__ == '__main__':

    short_options = "h"
    long_options = ["--help"]

    # Arguments management
    try:
        arguments, values = getopt.getopt(sys.argv[1:], short_options, long_options)
    except getopt.error as err:
        print(str(err))
        print_usage()
        sys.exit(2)
    required_args = [("-c", "--cpu"), ("-m", "--mem")]
    for required_arg in required_args:
        if required_arg not in arguments:
            print("Missing required argument : ", required_arg)
            print_usage()
            sys.exit(-1)
    for current_argument, current_value in arguments:
        if current_argument in ("-h", "--help"):
            print_usage()

    # Control        
    slice_duration = 3600 # default to 1h
    scope_duration = 86400 # default to 24h
    slices_per_scope= int(scope_duration / slice_duration)
    number_of_scope = 12 # default to 12

    # Entrypoint
    try:
        distribution_builder = DistributionBuilder(yaml_file="examples-scenario/scenario-vm-distribution.yml")
        usage_builder = UsageBuilder(yaml_file="examples-scenario/scenario-vm-profile.yml", slices_per_scope=slices_per_scope, number_of_scope=number_of_scope)
        workload_builder = WorkloadBuilder(yaml_file="examples-scenario/scenario-vm-workload.yml", slice_duration=slice_duration)

        generator = ExperimentGenerator(distribution_builder=distribution_builder, usage_builder=usage_builder, workload_builder=workload_builder)
        vm_list = generator.gen(cpu=256, mem=1024, number_of_scope=number_of_scope)

        generator.write_setup(vm_list)
        generator.write_setup_remote(vm_list)
        generator.write_workload_local(vm_list, slice_duration)
        generator.write_workload_remote(vm_list, slice_duration)

    except KeyboardInterrupt:
        print("Program interrupted")

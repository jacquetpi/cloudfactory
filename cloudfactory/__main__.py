import getopt, sys
from cloudfactory.distributionbuilder import DistributionBuilder
from cloudfactory.usagebuilder import UsageBuilder
from cloudfactory.workloadbuilder import WorkloadBuilder
from cloudfactory.experimentgenerator import ExperimentGenerator

if __name__ == '__main__':

    short_options = "h"
    long_options = ["--help"]
    usage = "python3 -m cloudfactory [--help]"

    # Arguments management
    try:
        arguments, values = getopt.getopt(sys.argv[1:], short_options, long_options)
    except getopt.error as err:
        print(str(err))
        print(usage)
        sys.exit(2)
    required_args = []
    for required_arg in required_args:
        if required_arg not in arguments:
            print("Missing required argument : ", required_arg, "in", required_args)
            print(usage)
            sys.exit(-1)
    for current_argument, current_value in arguments:
        if current_argument in ("-h", "--help"):
            print(usage)

    # Entrypoint
    try:
        distribution_builder = DistributionBuilder(yaml_file="examples-scenario/scenario-vm-distribution.yml")
        usage_builder = UsageBuilder(yaml_file="examples-scenario/scenario-vm-usage.yml")
        workload_builder = WorkloadBuilder(yaml_file="examples-scenario/scenario-vm-workload.yml", slice=900, scope=1800, timeout=1600)
        generator = ExperimentGenerator(distribution_builder=distribution_builder, usage_builder=usage_builder, workload_builder=workload_builder)
        generator.gen(cpu=256, mem=1024)

    except KeyboardInterrupt:
        print("Program interrupted")

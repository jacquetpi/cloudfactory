"""CloudFactory workload generator package.

This package turns scenario files (distribution, usage, workload YAML) and
generation targets (CPU/mem or VM count) into a set of VmModel instances with
usage and workload commands, and exports them to bash, CloudSim Plus, or CBTOOL.

Main entry point: run as ``python -m generator`` (see generator/__main__.py).
Core types: DistributionBuilder, UsageBuilder, WorkloadBuilder, ExperimentGenerator, VmModel.
Exporters: generator.exporter (ExporterBash, ExporterCloudSimPlus, ExporterCBTool).
"""

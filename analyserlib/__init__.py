"""CloudFactory analyser library for building scenarios from cloud traces.

This package provides tools to analyse VM trace datasets (e.g. Azure, Chameleon,
OVH) and produce scenario YAML files for the generator:

- distributionanalyzer: build VM CPU/memory flavor distributions over time and
  export scenario-vm-distribution.yml.
- usageanalyzer: cluster VMs by usage (avg/p95), compute arrival/departure/
  periodicity rates, and export scenario-vm-usage.yml.

Typical use: load a trace CSV into a pandas DataFrame, call the build_* and
convert_* functions, then pass the generated YAML files to the generator.
"""

"""Tests for analyserlib.distributionanalyzer."""
import os
import tempfile
import unittest

try:
    import pandas as pd
    import numpy as np
    import analyserlib.distributionanalyzer as distributionanalyzer
    HAS_DEPS = True
except ImportError:
    HAS_DEPS = False


@unittest.skipUnless(HAS_DEPS, "pandas/numpy/analyserlib not available")
class TestBuildCpuAndMemDistributionDataframes(unittest.TestCase):
    """Tests for build_cpu_and_mem_distribution_dataframes."""

    def test_returns_two_dataframes_with_timestamp(self):
        trace_df = pd.DataFrame({
            "vmcorecount": [1, 2, 1, 4, 2],
            "vmmemory": [1.75, 3.5, 1.75, 7, 3.5],
            "vmcreated": [0, 0, 3600, 3600, 7200],
            "vmdeleted": [7200, 7200, 7200, 7200, 10000],
        })
        cpu_df, mem_df = distributionanalyzer.build_cpu_and_mem_distribution_dataframes(
            trace_df,
            timestamp_begin=0,
            timestamp_end=7200,
            timestamp_step=3600,
        )
        self.assertIsInstance(cpu_df, pd.DataFrame)
        self.assertIsInstance(mem_df, pd.DataFrame)
        self.assertIn("timestamp", cpu_df.columns)
        self.assertIn("timestamp", mem_df.columns)
        self.assertEqual(len(cpu_df), 2)  # 2 time steps

    def test_respects_custom_columns(self):
        trace_df = pd.DataFrame({
            "cores": [1, 2],
            "mem_gb": [2.0, 4.0],
            "created": [0, 0],
            "deleted": [10000, 10000],
        })
        cpu_df, mem_df = distributionanalyzer.build_cpu_and_mem_distribution_dataframes(
            trace_df,
            col_flavor_cpu="cores",
            col_flavor_mem="mem_gb",
            col_vm_created="created",
            col_vm_deleted="deleted",
            timestamp_begin=0,
            timestamp_end=5000,
            timestamp_step=3600,
        )
        self.assertIn("1", cpu_df.columns)
        self.assertIn("2", cpu_df.columns)
        self.assertIn("2.0", mem_df.columns)
        self.assertIn("4.0", mem_df.columns)


@unittest.skipUnless(HAS_DEPS, "pandas/numpy/analyserlib not available")
class TestGetCpuAndMemAverageDistribution(unittest.TestCase):
    """Tests for get_cpu_and_mem_average_distribution."""

    def test_returns_cpu_and_mem_dataframes_with_freq(self):
        trace_df = pd.DataFrame({
            "vmcorecount": [1, 1, 2, 2, 4],
            "vmmemory": [1.75, 1.75, 3.5, 3.5, 7.0],
            "vmcreated": [0] * 5,
            "vmdeleted": [10000] * 5,
        })
        cpu_dist, mem_dist = distributionanalyzer.get_cpu_and_mem_average_distribution(
            trace_df,
            timestamp_begin=0,
            timestamp_end=5000,
            timestamp_step=3600,
        )
        self.assertIsInstance(cpu_dist, pd.DataFrame)
        self.assertIsInstance(mem_dist, pd.DataFrame)
        self.assertIn("freq", cpu_dist.columns)
        self.assertIn("freq", mem_dist.columns)
        self.assertIn("vmcorecount", cpu_dist.columns)
        self.assertIn("vmmemory", mem_dist.columns)
        self.assertGreater(len(cpu_dist), 0)
        self.assertGreater(len(mem_dist), 0)


@unittest.skipUnless(HAS_DEPS, "pandas/numpy/analyserlib not available")
class TestConvertDistributionToScenario(unittest.TestCase):
    """Tests for convert_distribution_to_scenario."""

    def test_writes_yaml_with_vm_distribution(self):
        cpu_dist = pd.DataFrame({"vmcorecount": [1, 2, 4], "freq": [0.5, 0.3, 0.2]})
        mem_dist = pd.DataFrame({"vmmemory": [1.75, 3.5, 7.0], "freq": [0.4, 0.4, 0.2]})
        with tempfile.NamedTemporaryFile(suffix=".yml", delete=False) as f:
            path = f.name
        try:
            distributionanalyzer.convert_distribution_to_scenario(
                cpu_dist, mem_dist, output_file=path
            )
            self.assertTrue(os.path.isfile(path))
            with open(path) as f:
                content = f.read()
            self.assertIn("vm_distribution", content)
            self.assertIn("config_cpu", content)
            self.assertIn("config_mem", content)
        finally:
            if os.path.isfile(path):
                os.remove(path)

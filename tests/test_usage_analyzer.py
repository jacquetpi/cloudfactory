"""Tests for analyserlib.usageanalyzer."""
import os
import tempfile
import unittest

try:
    import pandas as pd
    import numpy as np
    import analyserlib.usageanalyzer as usageanalyzer
    HAS_DEPS = True
except ImportError:
    HAS_DEPS = False


@unittest.skipUnless(HAS_DEPS, "pandas/numpy/analyserlib not available")
class TestBuildNScenario(unittest.TestCase):
    """Tests for build_n_scenario."""

    def test_returns_usage_distribution_and_labeled_trace(self):
        np.random.seed(42)
        n = 60
        trace_df = pd.DataFrame({
            "avgcpu": np.random.uniform(1, 80, n),
            "p95maxcpu": np.random.uniform(10, 100, n),
        })
        usage_dist, trace_labeled = usageanalyzer.build_n_scenario(trace_df, n_profile=3)
        self.assertIsInstance(usage_dist, pd.DataFrame)
        self.assertIsInstance(trace_labeled, pd.DataFrame)
        self.assertIn("label", trace_labeled.columns)
        self.assertEqual(len(trace_labeled), n)
        self.assertEqual(len(usage_dist), 3)
        self.assertIn("count", usage_dist.columns)
        self.assertIn("freq", usage_dist.columns)
        self.assertIn("bound_avg_lower", usage_dist.columns)
        self.assertIn("bound_per_lower", usage_dist.columns)

    def test_freq_sum_is_one(self):
        np.random.seed(42)
        trace_df = pd.DataFrame({
            "avgcpu": np.random.uniform(1, 50, 30),
            "p95maxcpu": np.random.uniform(20, 90, 30),
        })
        usage_dist, _ = usageanalyzer.build_n_scenario(trace_df, n_profile=2)
        self.assertAlmostEqual(usage_dist["freq"].sum(), 1.0, places=2)


@unittest.skipUnless(HAS_DEPS, "pandas/numpy/analyserlib not available")
class TestBuildArrivalAndDepartureRates(unittest.TestCase):
    """Tests for build_arrival_and_departure_rates_per_label."""

    def test_adds_ratio_columns(self):
        np.random.seed(42)
        n = 40
        trace_df = pd.DataFrame({
            "avgcpu": np.random.uniform(1, 80, n),
            "p95maxcpu": np.random.uniform(10, 100, n),
        })
        usage_dist, trace_labeled = usageanalyzer.build_n_scenario(trace_df, n_profile=2)
        base = trace_labeled["avgcpu"].min() - 1
        trace_labeled["vmcreated"] = np.random.randint(base, base + 86400 * 5, n)
        trace_labeled["vmdeleted"] = trace_labeled["vmcreated"] + np.random.randint(3600, 86400 * 2, n)
        usageanalyzer.build_arrival_and_departure_rates_per_label(
            usage_dist, trace_labeled,
            col_vm_created="vmcreated", col_vm_deleted="vmdeleted",
            scope_duration=86400,
        )
        self.assertIn("ratio_arriving", usage_dist.columns)
        self.assertIn("ratio_leaving", usage_dist.columns)


@unittest.skipUnless(HAS_DEPS, "pandas/numpy/analyserlib not available")
class TestConvertUsageToScenario(unittest.TestCase):
    """Tests for convert_usage_to_scenario."""

    def test_writes_yaml_with_vm_usage(self):
        usage_dist = pd.DataFrame({
            "label": [0, 1],
            "bound_avg_lower": [1.0, 20.0],
            "bound_avg_higher": [15.0, 80.0],
            "bound_per_lower": [5.0, 30.0],
            "bound_per_higher": [40.0, 95.0],
            "freq": [0.5, 0.5],
            "ratio_arriving": [0.1, 0.1],
            "ratio_leaving": [0.05, 0.05],
            "ratio_periodicity": [0.3, 0.3],
        })
        with tempfile.NamedTemporaryFile(suffix=".yml", delete=False) as f:
            path = f.name
        try:
            usageanalyzer.convert_usage_to_scenario(usage_dist, output_file=path)
            self.assertTrue(os.path.isfile(path))
            with open(path) as f:
                content = f.read()
            self.assertIn("vm_usage", content)
            self.assertIn("profile0", content)
            self.assertIn("profile1", content)
        finally:
            if os.path.isfile(path):
                os.remove(path)

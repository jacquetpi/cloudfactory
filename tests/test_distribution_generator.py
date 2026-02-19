"""Tests for generator.distributiongenerator (DistributionGenerator)."""
import unittest
import numpy as np
from generator.distributiongenerator import DistributionGenerator


class TestDistributionGenerator(unittest.TestCase):
    """Tests for Gaussian and heavy-tail distribution generation."""

    def setUp(self):
        np.random.seed(42)

    def test_generate_gaussian_distribution_from_avg_returns_list(self):
        dg = DistributionGenerator()
        x = dg.generate_gaussian_distribution_from_avg(20, 50)
        self.assertIsInstance(x, list)
        self.assertEqual(len(x), 1000)

    def test_generate_gaussian_distribution_from_avg_values_in_reasonable_range(self):
        dg = DistributionGenerator()
        x = dg.generate_gaussian_distribution_from_avg(20, 50)
        self.assertTrue(all(v >= 0 for v in x))
        self.assertLessEqual(np.percentile(x, 95), 55)  # allow some margin

    def test_generate_gaussian_handles_low_avg(self):
        dg = DistributionGenerator()
        x = dg.generate_gaussian_distribution_from_avg(1, 10)
        self.assertIsInstance(x, list)
        self.assertEqual(len(x), 1000)
        self.assertTrue(all(v >= 0 for v in x))

    def test_generate_heavy_tail_gaussian_for_deployments_returns_ndarray(self):
        dg = DistributionGenerator()
        out = dg.generate_heavy_tail_gaussian_for_deployments(100, 24)
        self.assertIsInstance(out, np.ndarray)
        self.assertEqual(len(out), 24)

    def test_generate_heavy_tail_gaussian_sum_near_target(self):
        dg = DistributionGenerator()
        out = dg.generate_heavy_tail_gaussian_for_deployments(50, 12)
        total = np.sum(out)
        self.assertGreaterEqual(total, 50 * 0.9)
        self.assertLessEqual(total, 50 * 1.1)

    def test_generate_heavy_tail_gaussian_non_negative(self):
        dg = DistributionGenerator()
        out = dg.generate_heavy_tail_gaussian_for_deployments(20, 10)
        self.assertTrue(np.all(out >= 0))

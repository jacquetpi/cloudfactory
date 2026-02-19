"""Tests for generator.usageprofile (UsageProfile)."""
import unittest
from generator.vmmodel import VmModel
from generator.usageprofile import UsageProfile


class TestUsageProfile(unittest.TestCase):
    """Tests for usage profile bounds, freq, and get_count."""

    def setUp(self):
        VmModel.vm_count = 0

    def _make_profile(self, freq=0.25, avg_min=1, avg_max=10, per_min=5, per_max=50,
                      arrival=0.0, departure=0.0, periodicity=0.3):
        d = {
            "freq": freq,
            "avg": {"min": avg_min, "max": avg_max},
            "per": {"min": per_min, "max": per_max},
            "rate": {"arrival": arrival, "departure": departure, "periodicity": periodicity},
        }
        return UsageProfile("p1", d, slices_per_scope=24, number_of_scope=2)

    def test_get_average_bounds(self):
        p = self._make_profile(avg_min=5, avg_max=15)
        self.assertEqual(p.get_average_bounds(), (5, 15))

    def test_get_percentile_bounds(self):
        p = self._make_profile(per_min=10, per_max=80)
        self.assertEqual(p.get_percentile_bounds(), (10, 80))

    def test_get_freq(self):
        p = self._make_profile(freq=0.5)
        self.assertEqual(p.get_freq(), 0.5)

    def test_get_count_filters_by_profile(self):
        p = self._make_profile()
        vms = [VmModel(cpu=1, mem=1) for _ in range(5)]
        vms[0].set_profile("p1")
        vms[1].set_profile("p1")
        vms[2].set_profile("other")
        vms[3].set_profile("p1")
        vms[4].set_profile("other")
        self.assertEqual(p.get_count(vms), 3)

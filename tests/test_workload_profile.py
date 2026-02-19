"""Tests for generator.workloadprofile (WorkloadProfile)."""
import unittest
from generator.vmmodel import VmModel
from generator.workloadprofile import WorkloadProfile


class TestWorkloadProfile(unittest.TestCase):
    """Tests for workload profile constraints and get_freq."""

    def setUp(self):
        VmModel.vm_count = 0

    def _make_profile(self, constraint, command="sleep §time", acronyms=None):
        workload_dict = {"constraint": constraint, "command": command}
        if acronyms:
            workload_dict["acronyms"] = acronyms
        return WorkloadProfile("test", workload_dict, {}, slice_duration=3600)

    def test_does_vm_verify_constraints_no_constraint(self):
        profile = self._make_profile({"freq": 0.2})
        vm = VmModel(cpu=2, mem=4)
        vm.set_profile("any")
        self.assertTrue(profile.does_vm_verify_constraints(vm))

    def test_does_vm_verify_constraints_profile_match(self):
        profile = self._make_profile({"freq": 0.2, "profile": ["low", "medium"]})
        vm = VmModel(cpu=2, mem=4)
        vm.set_profile("low")
        self.assertTrue(profile.does_vm_verify_constraints(vm))
        vm.set_profile("high")
        self.assertFalse(profile.does_vm_verify_constraints(vm))

    def test_does_vm_verify_constraints_mem_min_max(self):
        profile = self._make_profile({"freq": 0.2, "mem": {"min": 2, "max": 8}})
        vm = VmModel(cpu=2, mem=4)
        self.assertTrue(profile.does_vm_verify_constraints(vm))
        vm = VmModel(cpu=2, mem=1)
        self.assertFalse(profile.does_vm_verify_constraints(vm))
        vm = VmModel(cpu=2, mem=10)
        self.assertFalse(profile.does_vm_verify_constraints(vm))

    def test_does_vm_verify_constraints_cpu_min_max(self):
        profile = self._make_profile({"freq": 0.2, "cpu": {"min": 2, "max": 4}})
        vm = VmModel(cpu=2, mem=4)
        self.assertTrue(profile.does_vm_verify_constraints(vm))
        vm = VmModel(cpu=1, mem=4)
        self.assertFalse(profile.does_vm_verify_constraints(vm))
        vm = VmModel(cpu=8, mem=4)
        self.assertFalse(profile.does_vm_verify_constraints(vm))

    def test_get_freq(self):
        profile = self._make_profile({"freq": 0.33})
        self.assertEqual(profile.get_freq(), 0.33)

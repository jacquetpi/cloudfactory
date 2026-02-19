"""Tests for generator.distributionbuilder (DistributionBuilder)."""
import os
import unittest
from generator.distributionbuilder import DistributionBuilder
from generator.vmmodel import VmModel


class TestDistributionBuilder(unittest.TestCase):
    """Tests for VM set generation from distribution scenario."""

    @property
    def scenario_path(self):
        return os.path.join(os.path.dirname(__file__), "..", "examples-scenario", "scenario-vm-distribution-model.yml")

    def setUp(self):
        VmModel.vm_count = 0
        if not os.path.isfile(self.scenario_path):
            self.skipTest("Scenario file not found: %s" % self.scenario_path)

    def test_init_loads_yaml(self):
        builder = DistributionBuilder(yaml_file=self.scenario_path)
        self.assertIn("config_cpu", dir(builder))
        self.assertIsNotNone(builder.config_cpu)
        self.assertIsNotNone(builder.config_mem)

    def test_init_requires_yaml_file(self):
        with self.assertRaises(ValueError):
            DistributionBuilder()

    def test_generate_set_from_vm_number_returns_list_of_vm(self):
        builder = DistributionBuilder(yaml_file=self.scenario_path)
        vm_list = builder.generate_set_from_vm_number(10, display=False)
        self.assertIsInstance(vm_list, list)
        self.assertEqual(len(vm_list), 10)
        for vm in vm_list:
            self.assertIsInstance(vm, VmModel)
            self.assertIsInstance(vm.get_cpu(), (int, float))
            self.assertIsInstance(vm.get_mem(), (int, float))

    def test_generate_set_from_vm_number_respects_flavor_pool(self):
        builder = DistributionBuilder(yaml_file=self.scenario_path)
        vm_list = builder.generate_set_from_vm_number(100, display=False)
        cpus = {vm.get_cpu() for vm in vm_list}
        mems = {vm.get_mem() for vm in vm_list}
        self.assertTrue(cpus.issubset({1, 2, 4, 8}))
        self.assertTrue(mems.issubset({0.75, 1.75, 3.5, 7, 14}))

    def test_generate_set_from_config_returns_list(self):
        builder = DistributionBuilder(yaml_file=self.scenario_path)
        vm_list = builder.generate_set_from_config(32, 64, display=False)
        self.assertIsInstance(vm_list, list)
        self.assertGreater(len(vm_list), 0)
        total_cpu = sum(vm.get_cpu() for vm in vm_list)
        total_mem = sum(vm.get_mem() for vm in vm_list)
        self.assertLessEqual(total_cpu, 32 + 32)  # may be slightly under target
        self.assertGreater(total_cpu, 0)
        self.assertGreater(total_mem, 0)

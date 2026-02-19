"""Tests for generator.vmmodel (VmModel and VmModelEncoder)."""
import json
import unittest
from generator.vmmodel import VmModel, VmModelEncoder


class TestVmModel(unittest.TestCase):
    """Tests for VmModel creation, getters, setters, and serialization."""

    def setUp(self):
        # Reset class counter so test order does not affect id/name
        VmModel.vm_count = 0

    def test_init_requires_cpu_and_mem(self):
        with self.assertRaises(ValueError):
            VmModel()
        with self.assertRaises(ValueError):
            VmModel(cpu=2)
        with self.assertRaises(ValueError):
            VmModel(mem=4)

    def test_init_sets_cpu_mem_and_default_name_id(self):
        vm = VmModel(cpu=2, mem=4)
        self.assertEqual(vm.get_cpu(), 2)
        self.assertEqual(vm.get_mem(), 4)
        self.assertEqual(vm.get_id(), 0)
        self.assertEqual(vm.get_name(), "vm0")
        vm2 = VmModel(cpu=1, mem=1)
        self.assertEqual(vm2.get_id(), 1)
        self.assertEqual(vm2.get_name(), "vm1")

    def test_init_accepts_explicit_name_and_id(self):
        vm = VmModel(cpu=1, mem=2, id=99, name="custom")
        self.assertEqual(vm.get_id(), 99)
        self.assertEqual(vm.get_name(), "custom")

    def test_lifetime_getter_setter(self):
        vm = VmModel(cpu=1, mem=1)
        self.assertEqual(vm.get_lifetime(), 0)
        vm.set_lifetime(10)
        self.assertEqual(vm.get_lifetime(), 10)

    def test_postponed_start_getter_setter(self):
        vm = VmModel(cpu=1, mem=1)
        self.assertEqual(vm.get_postponed_start(), 0)
        vm.set_postponed_start(5)
        self.assertEqual(vm.get_postponed_start(), 5)

    def test_timesheet_getter_setter(self):
        vm = VmModel(cpu=1, mem=1)
        self.assertEqual(vm.get_timesheet(), {})
        ts = {0: [True, False], 1: [True, True]}
        vm.set_timesheet(ts)
        self.assertEqual(vm.get_timesheet(), ts)

    def test_profile_setter_getter(self):
        vm = VmModel(cpu=1, mem=1)
        self.assertIsNone(vm.get_profile())
        vm.set_profile("low")
        self.assertEqual(vm.get_profile(), "low")

    def test_usage_setter_getter(self):
        vm = VmModel(cpu=1, mem=1)
        self.assertEqual(vm.get_usage(), [])
        vm.set_usage([10, 20, 30])
        self.assertEqual(vm.get_usage(), [10, 20, 30])

    def test_workload_setter_getter(self):
        vm = VmModel(cpu=1, mem=1)
        self.assertIsNone(vm.get_workload())
        vm.set_workload("idle")
        self.assertEqual(vm.get_workload(), "idle")

    def test_commands_list_setter_getter(self):
        vm = VmModel(cpu=1, mem=1)
        self.assertEqual(vm.get_commands_list(), [])
        vm.set_commands_list(["cmd1", "cmd2"])
        self.assertEqual(vm.get_commands_list(), ["cmd1", "cmd2"])

    def test_periodicity_setter_getter(self):
        vm = VmModel(cpu=1, mem=1)
        self.assertFalse(vm.is_periodic())
        vm.set_periodicity(True)
        self.assertTrue(vm.is_periodic())


class TestVmModelEncoder(unittest.TestCase):
    """Tests for VmModelEncoder JSON serialization."""

    def setUp(self):
        VmModel.vm_count = 0

    def test_encoder_serializes_vm_as_dict(self):
        vm = VmModel(cpu=2, mem=4, name="v1")
        vm.set_profile("low")
        vm.set_usage([5, 10])
        out = json.dumps(vm, cls=VmModelEncoder)
        data = json.loads(out)
        self.assertIn("cpu", data)
        self.assertEqual(data["cpu"], 2)
        self.assertEqual(data["mem"], 4)
        self.assertEqual(data["name"], "v1")
        self.assertEqual(data["profile"], "low")
        self.assertEqual(data["usage"], [5, 10])

    def test_encoder_returns_none_for_non_vmmodel(self):
        self.assertIsNone(VmModelEncoder().default(42))
        self.assertIsNone(VmModelEncoder().default("x"))

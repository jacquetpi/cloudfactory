"""Tests for generator.experimentgenerator (ExperimentGenerator)."""
import os
import tempfile
import unittest
from generator.distributionbuilder import DistributionBuilder
from generator.usagebuilder import UsageBuilder
from generator.workloadbuilder import WorkloadBuilder
from generator.experimentgenerator import ExperimentGenerator
from generator.vmmodel import VmModel


class TestExperimentGenerator(unittest.TestCase):
    """Tests for experiment generation and write."""

    @property
    def dist_path(self):
        return os.path.join(os.path.dirname(__file__), "..", "examples-scenario", "scenario-vm-distribution-model.yml")

    @property
    def usage_path(self):
        return os.path.join(os.path.dirname(__file__), "..", "examples-scenario", "scenario-vm-usage-model.yml")

    @property
    def workload_path(self):
        return os.path.join(os.path.dirname(__file__), "..", "examples-workload", "scenario-vm-workload.yml")

    def setUp(self):
        VmModel.vm_count = 0
        if not all(os.path.isfile(p) for p in (self.dist_path, self.usage_path, self.workload_path)):
            self.skipTest("Example scenario/workload files not found")

    def _make_generator(self):
        dist_builder = DistributionBuilder(yaml_file=self.dist_path)
        usage_builder = UsageBuilder(
            yaml_file=self.usage_path,
            slices_per_scope=24,
            number_of_scope=2,
        )
        workload_builder = WorkloadBuilder(
            yaml_file=self.workload_path,
            slice_duration=3600,
        )
        return ExperimentGenerator(
            distribution_builder=dist_builder,
            usage_builder=usage_builder,
            workload_builder=workload_builder,
        )

    def test_gen_requires_cpu_mem_or_vm_number(self):
        gen = self._make_generator()
        with self.assertRaises(ValueError):
            gen.gen(number_of_scope=1)

    def test_gen_with_vm_number_returns_list(self):
        gen = self._make_generator()
        vm_list = gen.gen(vm_number=10, number_of_scope=1)
        self.assertIsInstance(vm_list, list)
        self.assertEqual(len(vm_list), 10)
        for vm in vm_list:
            self.assertIsInstance(vm, VmModel)
            self.assertIsNotNone(vm.get_profile())
            self.assertIsNotNone(vm.get_usage())
            self.assertIsNotNone(vm.get_commands_list())

    def test_gen_with_cpu_mem_returns_list(self):
        gen = self._make_generator()
        vm_list = gen.gen(cpu=8, mem=16, number_of_scope=1)
        self.assertIsInstance(vm_list, list)
        self.assertGreater(len(vm_list), 0)
        for vm in vm_list:
            self.assertIsInstance(vm, VmModel)
            self.assertIsNotNone(vm.get_profile())
            self.assertIsNotNone(vm.get_usage())

    def test_write_bash_creates_files(self):
        gen = self._make_generator()
        vm_list = gen.gen(vm_number=2, number_of_scope=1)
        with tempfile.TemporaryDirectory() as tmp:
            cwd = os.getcwd()
            try:
                os.chdir(tmp)
                gen.write(output_type="bash", vm_list=vm_list, slice_duration=3600)
                self.assertTrue(os.path.isfile("setup.sh"))
                self.assertTrue(os.path.isfile("workload-local.sh"))
                self.assertTrue(os.path.isfile("workload-remote.sh"))
            finally:
                os.chdir(cwd)

    def test_write_cloudsimplus_creates_files(self):
        gen = self._make_generator()
        vm_list = gen.gen(vm_number=2, number_of_scope=1)
        with tempfile.TemporaryDirectory() as tmp:
            cwd = os.getcwd()
            try:
                os.chdir(tmp)
                os.makedirs("static", exist_ok=True)
                with open("static/cloudsimplus.skeleton", "w") as f:
                    f.write("// minimal skeleton")
                gen.write(output_type="cloudsimplus", vm_list=vm_list, slice_duration=3600)
                self.assertTrue(os.path.isfile("CloudFactoryGeneratedWorkload.java"))
                self.assertTrue(os.path.isfile("vms.properties"))
                self.assertTrue(os.path.isfile("models.properties"))
            finally:
                os.chdir(cwd)

    def test_write_cbtool_creates_file(self):
        gen = self._make_generator()
        vm_list = gen.gen(vm_number=2, number_of_scope=1)
        with tempfile.TemporaryDirectory() as tmp:
            cwd = os.getcwd()
            try:
                os.chdir(tmp)
                os.makedirs("static", exist_ok=True)
                with open("static/cbtool.skeleton", "w") as f:
                    f.write("§commands§")
                gen.write(output_type="cbtool", vm_list=vm_list, slice_duration=3600)
                self.assertTrue(os.path.isfile("cloudfactory.cbtool"))
            finally:
                os.chdir(cwd)

    def test_write_invalid_type_raises(self):
        gen = self._make_generator()
        vm_list = gen.gen(vm_number=1, number_of_scope=1)
        with self.assertRaises(ValueError):
            gen.write(output_type="invalid", vm_list=vm_list, slice_duration=3600)

import sys

import pytest

from ducktools.lazyimporter import (
    LazyImporter,
    ModuleImport,
    FromImport,
    MultiFromImport,
    TryExceptImport,
    TryExceptFromImport,
)


class TestDirectImports:
    def test_module_import(self):
        """
        Test Basic Module import occurs when expected
        """
        laz = LazyImporter(
            [
                ModuleImport("example_1"),
            ]
        )

        assert "example_1" not in sys.modules
        laz.example_1
        assert "example_1" in sys.modules

        # Check the import is the correct object
        import example_1  # noqa  # pyright: ignore

        assert example_1 is laz.example_1

    def test_module_import_asname(self):
        laz = LazyImporter([ModuleImport("example_1", asname="ex1")])

        import example_1  # noqa  # pyright: ignore

        assert example_1 is laz.ex1

    def test_from_import(self):
        """
        Test a basic from import from a module
        """
        laz = LazyImporter(
            [
                FromImport("example_2", "item", asname="i"),
            ]
        )

        assert "example_2" not in sys.modules
        laz.i
        assert "example_2" in sys.modules

        assert laz.i == "example"

        import example_2  # noqa  # pyright: ignore

        assert example_2.item is laz.i


    def test_imports_submod_asname(self):
        laz_sub = LazyImporter([ModuleImport("ex_mod.ex_submod", asname="ex_submod")])

        assert laz_sub.ex_submod.name == "ex_submod"

    def test_submod_from(self):
        """
        Test a from import from a submodule
        """
        laz = LazyImporter(
            [
                FromImport("ex_mod.ex_submod", "name"),
            ]
        )

        assert laz.name == "ex_submod"

    def test_submod_multifrom(self):
        """
        Test a basic multi from import
        """
        laz = LazyImporter(
            [
                MultiFromImport("ex_mod.ex_submod", ["name", ("name2", "othername")]),
            ]
        )

        assert laz.name == "ex_submod"
        assert laz.othername == "ex_submod2"

    def test_try_except_import(self):
        """
        Test a basic try/except import
        """
        # When the first import fails
        laz = LazyImporter(
            [
                TryExceptImport("module_does_not_exist", "ex_mod", "ex_mod"),
            ]
        )

        assert laz.ex_mod.name == "ex_mod"

        # When the first import succeeds
        laz2 = LazyImporter(
            [
                TryExceptImport("ex_mod", "ex_othermod", "ex_mod"),
            ]
        )

        assert laz2.ex_mod.name == "ex_mod"

    def test_try_except_submod_import(self):
        """
        Test a try/except import with submodules
        """
        laz = LazyImporter(
            [
                TryExceptImport(
                    "module_does_not_exist", "ex_mod.ex_submod", "ex_submod"
                ),
            ]
        )

        assert laz.ex_submod.name == "ex_submod"

    def test_try_except_from_import(self):
        laz = LazyImporter(
            [TryExceptFromImport("ex_mod", "name", "ex_othermod", "name", "name")]
        )

        assert laz.name == "ex_mod"

        laz = LazyImporter(
            [
                TryExceptFromImport(
                    "module_does_not_exist", "name", "ex_mod.ex_submod", "name", "name"
                )
            ]
        )

        assert laz.name == "ex_submod"


class TestRelativeImports:
    def test_relative_import(self):
        import example_modules.lazy_submod_ex as lse

        laz = lse.lazy_submod_from_import()
        assert laz.name == "ex_submod"

        laz = lse.lazy_submod_multi_from_import()
        assert laz.name == "ex_submod"
        assert laz.othername == "ex_submod2"

    def test_submod_relative_import(self):
        from example_modules.ex_othermod import laz

        assert laz.submod_name == "ex_submod"

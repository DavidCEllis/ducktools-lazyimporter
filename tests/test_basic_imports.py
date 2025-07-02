import sys

import pytest

import ducktools.lazyimporter as lazyimporter

from ducktools.lazyimporter import (
    LazyImporter,
    ModuleImport,
    FromImport,
    MultiFromImport,
    TryExceptImport,
    TryExceptFromImport,
    TryFallbackImport,
    get_importer_state,
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
        import example_1  # type: ignore

        assert example_1 is laz.example_1

    def test_module_import_asname(self):
        laz = LazyImporter([ModuleImport("example_1", asname="ex1")])

        import example_1  # type: ignore

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

        import example_2  # type: ignore

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

    def test_try_fallback_import(self):
        import ex_mod  # type: ignore
        import ex_mod.ex_submod  # type: ignore

        test_obj = object()

        laz = LazyImporter(
            [TryFallbackImport("ex_mod", test_obj)]
        )

        assert laz.ex_mod is ex_mod

        laz = LazyImporter(
            [TryFallbackImport("ex_mod", test_obj, "module_name")]
        )

        assert laz.module_name is ex_mod

        laz = LazyImporter(
            [TryFallbackImport("module_does_not_exist", test_obj)]
        )

        assert laz.module_does_not_exist is test_obj

        laz = LazyImporter(
            [TryFallbackImport("module_does_not_exist", test_obj, "module_name")]
        )

        assert laz.module_name is test_obj

        laz = LazyImporter(
            [TryFallbackImport("ex_mod.ex_submod", None, "ex_submod")]
        )

        assert laz.ex_submod == ex_mod.ex_submod


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


class TestEager:
    def test_eager_process(self):
        laz = LazyImporter([ModuleImport("functools")], eager_process=False)

        assert "_importers" not in vars(laz)

        laz = LazyImporter([ModuleImport("functools")], eager_process=True)

        assert "_importers" in vars(laz)

    def test_eager_import(self):
        laz = LazyImporter([ModuleImport("functools")], eager_import=False)

        assert "functools" not in vars(laz)

        laz = LazyImporter([ModuleImport("functools")], eager_import=True)

        assert "functools" in vars(laz)

    def test_eager_process_glob(self):
        initial_state = lazyimporter.EAGER_PROCESS

        lazyimporter.EAGER_PROCESS = False

        # EAGER_PROCESS = False and no value - should lazily process
        laz = LazyImporter([ModuleImport("functools")])
        assert "_importers" not in vars(laz)

        # EAGER_PROCESS = False and eager_process = False - should lazily process
        laz = LazyImporter([ModuleImport("functools")], eager_process=False)
        assert "_importers" not in vars(laz)

        # EAGER_PROCESS = False and eager_process = True - should eagerly process
        laz = LazyImporter([ModuleImport("functools")], eager_process=True)
        assert "_importers" in vars(laz)

        lazyimporter.EAGER_PROCESS = True

        # EAGER_PROCESS = True and no value - should eagerly process
        laz = LazyImporter([ModuleImport("functools")])
        assert "_importers" in vars(laz)

        # EAGER_PROCESS = True and eager_process = False - should lazily process
        laz = LazyImporter([ModuleImport("functools")], eager_process=False)
        assert "_importers" not in vars(laz)

        # EAGER_PROCESS = True and eager_process = True - should eagerly process
        laz = LazyImporter([ModuleImport("functools")], eager_process=True)
        assert "_importers" in vars(laz)

        # Restore state
        lazyimporter.EAGER_PROCESS = initial_state

    def test_eager_import_glob(self):
        initial_state = lazyimporter.EAGER_IMPORT

        lazyimporter.EAGER_IMPORT = False

        # EAGER_IMPORT = False and no value - should lazily import
        laz = LazyImporter([ModuleImport("functools")])
        assert "functools" not in vars(laz)

        # EAGER_IMPORT = False and eager_import = False - should lazily import
        laz = LazyImporter([ModuleImport("functools")], eager_import=False)
        assert "functools" not in vars(laz)

        # EAGER_IMPORT = False and eager_import = True - should eagerly import
        laz = LazyImporter([ModuleImport("functools")], eager_import=True)
        assert "functools" in vars(laz)

        lazyimporter.EAGER_IMPORT = True

        # EAGER_IMPORT = True and no value - should eagerly import
        laz = LazyImporter([ModuleImport("functools")])
        assert "functools" in vars(laz)

        # EAGER_IMPORT = True and eager_import = False - should lazily import
        laz = LazyImporter([ModuleImport("functools")], eager_import=False)
        assert "functools" not in vars(laz)

        # EAGER_IMPORT = True and eager_import = True - should eagerly import
        laz = LazyImporter([ModuleImport("functools")], eager_import=True)
        assert "functools" in vars(laz)

        # Restore state
        lazyimporter.EAGER_IMPORT = initial_state

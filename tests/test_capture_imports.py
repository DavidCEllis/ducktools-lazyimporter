import builtins
import sys

import unittest.mock as mock

import pytest

from ducktools.lazyimporter import LazyImporter, ModuleImport, MultiFromImport
from ducktools.lazyimporter.capture import capture_imports, CaptureError


# Lazy Import capture must be at module level
# So setup code is at module level and tests are interspersed

# test_importer_placed
laz = LazyImporter()
with capture_imports(laz, auto_export=False) as capture_check:
    capture_import_func = builtins.__import__


def test_importer_placed():
    assert capture_check.import_func == capture_import_func


del laz

# test_module_capture
laz = LazyImporter()
with capture_imports(laz, auto_export=False):
    import functools


def test_module_capture(laz=laz):
    faked_imports = [ModuleImport("functools")]
    assert laz._imports == faked_imports


del laz

# test_module_as_capture
laz = LazyImporter()
with capture_imports(laz, auto_export=False):
    import functools as ft


def test_module_as_capture(laz=laz):
    faked_imports = [ModuleImport("functools", "ft")]
    assert laz._imports == faked_imports


del laz

# test_submodule_as_capture
laz = LazyImporter()
with capture_imports(laz, auto_export=False):
    import importlib.util as util


def test_submodule_as_capture(laz=laz):
    faked_imports = [ModuleImport("importlib.util", "util")]
    assert laz._imports == faked_imports


del laz

# test_from_capture
laz = LazyImporter()
with capture_imports(laz, auto_export=False):
    from functools import partial


def test_from_capture(laz=laz):
    faked_imports = [MultiFromImport("functools", [("partial", "partial")])]
    assert laz._imports == faked_imports


del laz

# test_from_submod_capture
laz = LazyImporter()
with capture_imports(laz, auto_export=False):
    from importlib.util import spec_from_loader as sfl


def test_from_submod_capture(laz=laz):
    faked_imports = [
        MultiFromImport("importlib.util", [("spec_from_loader", "sfl")])
    ]
    assert laz._imports == faked_imports


del laz

# test_from_as_capture
laz = LazyImporter()
with capture_imports(laz, auto_export=False):
    from functools import partial as part


def test_from_as_capture(laz=laz):
    faked_imports = [
        MultiFromImport("functools", [("partial", "part")])
    ]
    assert laz._imports == faked_imports


del laz

# test_captured_multiple_names
laz = LazyImporter()
with capture_imports(laz, auto_export=False):
    from functools import partial as part, lru_cache as lru


def test_captured_multiple_names(laz=laz):
    faked_imports = [
        MultiFromImport(
            "functools",
            [("partial", "part"), ("lru_cache", "lru")]
        )
    ]
    assert laz._imports == faked_imports


del laz

# test_captured_multiple_names_separate_statements
laz = LazyImporter()
with capture_imports(laz, auto_export=False):
    from functools import partial as part
    from functools import lru_cache as lru


def test_captured_multiple_names_separate_statements(laz=laz):
    faked_imports = [
        MultiFromImport(
            "functools",
            [("partial", "part"), ("lru_cache", "lru")]
        )
    ]

    assert laz._imports == faked_imports


del laz


class TestExceptions:
    def test_raises_in_function(self):
        laz = LazyImporter()
        with pytest.raises(CaptureError):
            with capture_imports(laz, auto_export=False):
                pass

    def test_raises_in_class(self):
        with pytest.raises(CaptureError):
            import example_modules.captures.error_raises_in_class

    def test_raises_mismatch(self):
        with pytest.raises(CaptureError):
            import example_modules.captures.error_globs_mismatch

    def test_raises_starimport(self):
        with pytest.raises(CaptureError):
            import example_modules.captures.error_star_import

    def test_raises_reentry(self):
        with pytest.raises(CaptureError):
            import example_modules.captures.error_reuse

    def test_raises_getattr_exists(self):
        with pytest.raises(CaptureError):
            import example_modules.captures.error_getattr_defined

    def test_raises_dir_exists(self):
        with pytest.raises(CaptureError):
            import example_modules.captures.error_dir_defined

    def test_raises_submodule_import(self):
        with pytest.raises(CaptureError):
            import example_modules.captures.error_submodule_import

    def test_raises_submodule_import_before_module(self):
        with pytest.raises(CaptureError):
            import example_modules.captures.error_submodule_import_before_module

    def test_raises_reused_from_name(self):
        with pytest.raises(CaptureError):
            import example_modules.captures.error_reused_from_name

    def test_import_replaced(self):
        importer = builtins.__import__
        with pytest.raises(CaptureError):
            import example_modules.captures.error_import_replaced

        assert builtins.__import__ is importer

    def test_mock_no_getframe(self):
        # Pretend not to have getframe to check error
        with mock.patch("ducktools.lazyimporter.capture.sys") as sys_mock:
            del sys_mock._getframe

            laz = LazyImporter()
            with pytest.raises(CaptureError):
                cap = capture_imports(laz, auto_export=False)


# Imports captured from other modules
class TestModuleCaptures:
    def test_laz_values(self):
        import functools
        from example_modules import captures
        assert captures.laz._imports == [
            ModuleImport("functools"),
            MultiFromImport(
                ".",
                [("import_target", "import_target")])
        ]
        assert captures.functools is functools

    def test_real_import(self):
        assert "example_modules.captures.func_import_target" in sys.modules

    def test_ignore_import_inside_function(self):
        import functools, typing
        import example_modules.captures.ignore_import_in_function as mod

        assert mod.laz._imports == [ModuleImport("collections")]

        assert mod.inner_import is functools
        assert mod.InnerClass.typing is typing

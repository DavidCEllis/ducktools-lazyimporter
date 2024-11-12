import builtins
import sys

from ducktools.lazyimporter import LazyImporter, ModuleImport, MultiFromImport
from ducktools.lazyimporter.capture import capture_imports

from example_modules import captures


class TestBasicCaptures:
    def test_importer_placed(self):
        laz = LazyImporter()
        with capture_imports(laz, auto_export=False) as capturer:
            assert builtins.__import__ is capturer.import_func

    def test_module_capture(self):
        faked_imports = [
            ModuleImport("functools")
        ]

        laz = LazyImporter()

        with capture_imports(laz, auto_export=False):
            import functools

        assert laz._imports == faked_imports

    def test_module_as_capture(self):
        faked_imports = [
            ModuleImport("functools", "ft")
        ]
        laz = LazyImporter()
        with capture_imports(laz, auto_export=False):
            import functools as ft

        assert laz._imports == faked_imports

    def test_submodule_as_capture(self):
        faked_imports = [
            ModuleImport("importlib.util", "util")
        ]

        laz = LazyImporter()
        with capture_imports(laz, auto_export=False):
            import importlib.util as util

        assert laz._imports == faked_imports

    def test_from_capture(self):
        faked_imports = [
            MultiFromImport("functools", [("partial", "partial")])
        ]

        laz = LazyImporter()
        with capture_imports(laz, auto_export=False):
            from functools import partial

        assert laz._imports == faked_imports

    def test_from_submod_capture(self):
        faked_imports = [
            MultiFromImport("importlib.util", [("spec_from_loader", "sfl")])
        ]

        laz = LazyImporter()
        with capture_imports(laz, auto_export=False):
            from importlib.util import spec_from_loader as sfl

        assert laz._imports == faked_imports

    def test_from_as_capture(self):
        faked_imports = [
            MultiFromImport("functools", [("partial", "part")])
        ]

        laz = LazyImporter()
        with capture_imports(laz, auto_export=False):
            from functools import partial as part

        assert laz._imports == faked_imports

    def test_captured_multiple_names(self):
        faked_imports = [
            MultiFromImport(
                "functools",
                [("partial", "part"), ("lru_cache", "lru")])
        ]

        laz = LazyImporter()
        with capture_imports(laz, auto_export=False):
            from functools import partial as part, lru_cache as lru

        assert laz._imports == faked_imports

    def test_captured_multiple_names_separate_statements(self):
        faked_imports = [
            MultiFromImport(
                "functools",
                [("partial", "part"), ("lru_cache", "lru")]
            )
        ]

        laz = LazyImporter()
        with capture_imports(laz, auto_export=False):
            from functools import partial as part
            from functools import lru_cache as lru

        assert laz._imports == faked_imports


class TestModuleCaptures:
    def test_laz_values(self):
        assert captures.laz._imports == [
            ModuleImport("functools"),
            MultiFromImport(
                ".",
                [("import_target", "import_target")])
        ]

    def test_real_import(self):
        assert "example_modules.captures.func_import_target" in sys.modules

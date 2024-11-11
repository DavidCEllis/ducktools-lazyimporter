import builtins

from ducktools.lazyimporter import LazyImporter, ModuleImport, MultiFromImport
from ducktools.lazyimporter.capture import capture_imports


class TestBasicCaptures:
    def test_importer_placed(self):
        laz = LazyImporter()
        with capture_imports(laz) as capturer:
            assert builtins.__import__ is capturer.import_func

    def test_module_capture(self):
        faked_imports = [
            ModuleImport("functools")
        ]

        laz = LazyImporter()

        with capture_imports(laz):
            import functools

        assert laz._imports == faked_imports

    def test_module_as_capture(self):
        faked_imports = [
            ModuleImport("functools", "ft")
        ]
        laz = LazyImporter()
        with capture_imports(laz):
            import functools as ft

        assert laz._imports == faked_imports

    def test_submodule_as_capture(self):
        faked_imports = [
            ModuleImport("importlib.util", "util")
        ]

        laz = LazyImporter()
        with capture_imports(laz):
            import importlib.util as util

        assert laz._imports == faked_imports

    def test_from_capture(self):
        faked_imports = [
            MultiFromImport("functools", [("partial", "partial")])
        ]

        laz = LazyImporter()
        with capture_imports(laz):
            from functools import partial

        assert laz._imports == faked_imports

    def test_from_as_capture(self):
        faked_imports = [
            MultiFromImport("functools", [("partial", "part")])
        ]

        laz = LazyImporter()
        with capture_imports(laz):
            from functools import partial as part

        assert laz._imports == faked_imports

    def test_captured_multiple_names(self):
        faked_imports = [
            MultiFromImport(
                "functools",
                [("partial", "part"), ("lru_cache", "lru")])
        ]

        laz = LazyImporter()
        with capture_imports(laz):
            from functools import partial as part, lru_cache as lru

        assert laz._imports == faked_imports

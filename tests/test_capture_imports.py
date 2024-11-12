import builtins
import sys

from ducktools.lazyimporter import LazyImporter, ModuleImport, MultiFromImport
from ducktools.lazyimporter.capture import capture_imports

from example_modules import captures

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


# Imports captured from other modules
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

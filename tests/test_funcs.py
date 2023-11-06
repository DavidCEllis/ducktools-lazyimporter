"""
Test the external functions
"""

from ducktools.lazyimporter import (
    ModuleImport,
    FromImport,
    MultiFromImport,
    TryExceptImport,
    _SubmoduleImports,
    MultiFromImport,
    get_importer_state,
    get_module_funcs,
    LazyImporter,
)


class TestImporterState:
    def test_module_importer_state(self):
        laz = LazyImporter([ModuleImport("collections")])

        state = get_importer_state(laz)

        assert state["lazy_attributes"] == ["collections"]
        assert state["imported_attributes"] == {}

        collections_mod = laz.collections

        state = get_importer_state(laz)

        assert state["lazy_attributes"] == []
        assert state["imported_attributes"] == {"collections": collections_mod}


class TestModuleFuncs:
    def test_getattr_func(self):
        import collections

        laz = LazyImporter([ModuleImport("collections")])

        getattr_func, _ = get_module_funcs(laz)

        assert getattr_func("collections") is collections

    def test_dir_func(self):
        laz = LazyImporter([ModuleImport("collections")])

        _, dir_func = get_module_funcs(laz)

        assert dir_func() == ["collections"]

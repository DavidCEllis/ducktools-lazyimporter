"""
Test the external functions
"""

from ducktools.lazyimporter import (
    ModuleImport,
    FromImport,
    MultiFromImport,
    TryExceptImport,
    MultiFromImport,
    get_importer_state,
    get_module_funcs,
    LazyImporter,
    force_imports,
    extend_imports,
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

        dir_vals = sorted(["collections", *globals().keys()])

        assert dir_func() == dir_vals

    def test_getattr_module_func(self):
        import example_modules.ex_othermod as ex_othermod  # noqa  # pyright: ignore

        assert ex_othermod.submod_name == "ex_submod"

    def test_dir_module_func(self):
        import example_modules.ex_othermod as ex_othermod  # noqa  # pyright: ignore

        assert "name" in dir(ex_othermod)
        assert "submod_name" in dir(ex_othermod)


def test_force_imports():
    laz = LazyImporter([FromImport("example_modules.ex_mod", "name")])

    assert get_importer_state(laz) == {
        "imported_attributes": {},
        "lazy_attributes": ["name"],
    }

    force_imports(laz)

    assert get_importer_state(laz) == {
        "imported_attributes": {"name": "ex_mod"},
        "lazy_attributes": [],
    }

class TestExtendImports:
    def test_lazy_example(self):
        import functools

        laz = LazyImporter([ModuleImport("functools")])

        extend_imports(laz, [ModuleImport("collections")])

        state = get_importer_state(laz)
        assert state["imported_attributes"] == {}
        assert sorted(state["lazy_attributes"]) == sorted(["functools", "collections"])

        _ = laz.functools

        extend_imports(laz, [ModuleImport("itertools")])

        state = get_importer_state(laz)
        assert state["imported_attributes"] == {"functools": functools}
        assert sorted(state["lazy_attributes"]) == sorted(["itertools", "collections"])

    def test_eager_example(self):
        import functools, itertools, collections

        laz = LazyImporter([ModuleImport("functools")], eager_import=True)

        extend_imports(laz, [ModuleImport("collections")])

        state = get_importer_state(laz)
        assert state["imported_attributes"] == {
            "functools": functools,
            "collections": collections
        }
        assert state["lazy_attributes"] == []

        _ = laz.functools

        extend_imports(laz, [ModuleImport("itertools")])

        state = get_importer_state(laz)
        assert state["imported_attributes"] == {
            "functools": functools,
            "itertools": itertools,
            "collections": collections,
        }
        assert state["lazy_attributes"] == []

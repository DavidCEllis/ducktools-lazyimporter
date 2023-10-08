from lazy_importer import (
    ModuleImport, FromImport, LazyImporter, _SubmoduleImports, MultiFromImport
)


def test_equal_module():
    mod1 = ModuleImport("collections")
    mod2 = ModuleImport("collections")

    assert mod1 == mod2

    mod2 = ModuleImport("collections", "c")

    assert mod1 != mod2


def test_no_duplication():
    importer = LazyImporter([
        ModuleImport("collections"),
        ModuleImport("collections")
    ])

    assert dir(importer) == ["collections"]
    assert importer._importers == {"collections": _SubmoduleImports("collections")}


def test_submodule_gather():
    importer = LazyImporter([
        ModuleImport("collections.abc"),
    ])

    assert dir(importer) == ["collections"]

    assert importer._importers == {
        "collections":  _SubmoduleImports("collections", {"collections.abc"})
    }


def test_asname_gather():
    importer = LazyImporter([
        ModuleImport("collections.abc", "abc"),
    ])

    assert dir(importer) == ["abc"]
    assert importer._importers == {
        "abc": ModuleImport("collections.abc", "abc")
    }



def test_from_gather():
    importer = LazyImporter([
        FromImport("dataclasses", "dataclass"),
        FromImport("dataclasses", "dataclass", "dc")
    ])

    assert dir(importer) == ["dataclass", "dc"]

    assert importer._importers == {
        "dataclass": FromImport("dataclasses", "dataclass"),
        "dc": FromImport("dataclasses", "dataclass", "dc"),
    }


def test_mixed_gather():
    importer = LazyImporter([
        ModuleImport("collections"),
        ModuleImport("collections.abc"),
        ModuleImport("functools", "ft"),
        FromImport("dataclasses", "dataclass"),
        FromImport("typing", "NamedTuple", "nt"),
    ])

    assert dir(importer) == ["collections", "dataclass", "ft", "nt"]

    assert importer._importers == {
        "collections": _SubmoduleImports("collections", {"collections.abc"}),
        "dataclass": FromImport("dataclasses", "dataclass"),
        "ft": ModuleImport("functools", "ft"),
        "nt": FromImport("typing", "NamedTuple", "nt")
    }


def test_multi_from():
    importer = LazyImporter([
        MultiFromImport(
            "collections", ["defaultdict", ("namedtuple", "nt"), "OrderedDict"]
        ),
        FromImport("Functools", "partial"),
        ModuleImport("importlib.util"),
    ])

    assert dir(importer) == sorted([
        "defaultdict", "nt", "ordereddict", "partial", "importlib"
    ])

    assert importer._importers == {
        "defaultdict": FromImport("collections", "defaultdict"),
        "nt": FromImport("collections")
    }
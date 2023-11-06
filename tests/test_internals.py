import itertools

from ducktools.lazyimporter import (
    ModuleImport,
    FromImport,
    MultiFromImport,
    TryExceptImport,
    LazyImporter,
    _SubmoduleImports,
    MultiFromImport,
)


class TestImporterDunders:
    def test_equal_module(self):
        mod1 = ModuleImport("collections")
        mod2 = ModuleImport("collections")

        assert mod1 == mod2

        mod2 = ModuleImport("collections", "c")

        assert mod1 != mod2

    def test_equal_from(self):
        from1 = FromImport("collections", "namedtuple")
        from2 = FromImport("collections", "namedtuple")

        assert from1 == from2

        from2 = FromImport("collections", "defaultdict")

        assert from1 != from2

    def test_equal_multifrom(self):
        mf1 = MultiFromImport("collections", ["namedtuple", "defaultdict"])
        mf2 = MultiFromImport("collections", ["namedtuple", "defaultdict"])

        assert mf1 == mf2

        mf2 = MultiFromImport("collections", ["namedtuple"])

        assert mf1 != mf2

    def test_equal_tryexcept(self):
        te1 = TryExceptImport("tomllib", "tomli", "tomllib")
        te2 = TryExceptImport("tomllib", "tomli", "tomllib")

        assert te1 == te2

        te2 = TryExceptImport("dataclasses", "attrs", "dataclasses")
        assert te1 != te2

    def test_unequal_different_types(self):
        mod1 = ModuleImport("collections")
        from1 = FromImport("collections", "namedtuple")
        mf1 = MultiFromImport("collections", ["namedtuple", "defaultdict"])
        te1 = TryExceptImport("tomllib", "tomli", "tomllib")

        combs = itertools.combinations([mod1, from1, mf1, te1], 2)

        for i1, i2 in combs:
            assert i1 != i2


def test_no_duplication():
    importer = LazyImporter([ModuleImport("collections"), ModuleImport("collections")])

    assert dir(importer) == ["collections"]
    assert importer._importers == {"collections": _SubmoduleImports("collections")}


def test_submodule_gather():
    importer = LazyImporter(
        [
            ModuleImport("collections.abc"),
        ]
    )

    assert dir(importer) == ["collections"]

    assert importer._importers == {
        "collections": _SubmoduleImports("collections", {"collections.abc"})
    }


def test_asname_gather():
    importer = LazyImporter(
        [
            ModuleImport("collections.abc", "abc"),
        ]
    )

    assert dir(importer) == ["abc"]
    assert importer._importers == {"abc": ModuleImport("collections.abc", "abc")}


def test_from_gather():
    importer = LazyImporter(
        [
            FromImport("dataclasses", "dataclass"),
            FromImport("dataclasses", "dataclass", "dc"),
        ]
    )

    assert dir(importer) == ["dataclass", "dc"]

    assert importer._importers == {
        "dataclass": FromImport("dataclasses", "dataclass"),
        "dc": FromImport("dataclasses", "dataclass", "dc"),
    }


def test_mixed_gather():
    importer = LazyImporter(
        [
            ModuleImport("collections"),
            ModuleImport("collections.abc"),
            ModuleImport("functools", "ft"),
            FromImport("dataclasses", "dataclass"),
            FromImport("typing", "NamedTuple", "nt"),
        ]
    )

    assert dir(importer) == ["collections", "dataclass", "ft", "nt"]

    assert importer._importers == {
        "collections": _SubmoduleImports("collections", {"collections.abc"}),
        "dataclass": FromImport("dataclasses", "dataclass"),
        "ft": ModuleImport("functools", "ft"),
        "nt": FromImport("typing", "NamedTuple", "nt"),
    }


def test_multi_from():
    multi_from = MultiFromImport(
        "collections", ["defaultdict", ("namedtuple", "nt"), "OrderedDict"]
    )
    from_imp = FromImport("functools", "partial")
    mod_imp = ModuleImport("importlib.util")

    # Resulting submodule import
    submod_imp = _SubmoduleImports("importlib", {"importlib.util"})

    importer = LazyImporter([multi_from, from_imp, mod_imp])

    assert dir(importer) == sorted(
        ["defaultdict", "nt", "OrderedDict", "partial", "importlib"]
    )

    assert importer._importers == {
        "defaultdict": multi_from,
        "nt": multi_from,
        "OrderedDict": multi_from,
        "partial": from_imp,
        "importlib": submod_imp,
    }


def test_relative_basename():
    from_imp_level0 = FromImport("mod", "obj")
    from_imp_level1 = FromImport(".mod", "obj")
    from_imp_level2 = FromImport("..mod", "obj")

    assert from_imp_level0.import_level == 0
    assert from_imp_level1.import_level == 1
    assert from_imp_level2.import_level == 2

    assert (
        from_imp_level0.module_name_noprefix
        == from_imp_level1.module_name_noprefix
        == from_imp_level2.module_name_noprefix
        == "mod"
    )

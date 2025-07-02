import itertools
from unittest.mock import patch

import pytest

from ducktools.lazyimporter import (
    ModuleImport,
    FromImport,
    MultiFromImport,
    TryExceptImport,
    TryExceptFromImport,
    TryFallbackImport,
    _ImporterGrouper,
    LazyImporter,
)


class TestImporterDunders:
    def test_equal_module(self):
        mod1 = ModuleImport("collections")
        mod2 = ModuleImport("collections")

        assert mod1 == mod2

        mod2 = ModuleImport("collections", "c")

        assert mod1 != mod2

        mod3 = ModuleImport("collections", "c")
        assert mod3 == mod2

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

    def test_equal_tryexceptfrom(self):
        te1 = TryExceptFromImport("tomllib", "loads", "tomli", "loads", "loads")
        te2 = TryExceptFromImport("tomllib", "loads", "tomli", "loads", "loads")

        assert te1 == te2

        te2 = TryExceptFromImport(
            "attrs", "define", "dataclasses", "dataclass", "define"
        )
        assert te1 != te2

    def test_equal_tryfallback(self):
        tf1 = TryFallbackImport("tomllib", None)
        tf2 = TryFallbackImport("tomllib", None)

        assert tf1 == tf2

        tf3 = TryFallbackImport("tomli", None)
        assert tf1 != tf3

    def test_unequal_different_types(self):
        mod1 = ModuleImport("collections")
        from1 = FromImport("collections", "namedtuple")
        mf1 = MultiFromImport("collections", ["namedtuple", "defaultdict"])
        te1 = TryExceptImport("tomllib", "tomli", "tomllib")
        tef1 = TryExceptFromImport("tomllib", "loads", "tomli", "loads", "loads")
        tf1 = TryFallbackImport("tomllib", None)

        combs = itertools.combinations([mod1, from1, mf1, te1, tef1, tf1], 2)

        for i1, i2 in combs:
            assert i1 != i2

    def test_import_repr_module(self):
        mod1 = ModuleImport(module_name='collections')
        mod1str = "ModuleImport(module_name='collections', asname='collections')"

        assert repr(mod1) == mod1str

    def test_import_repr_from(self):
        from1 = FromImport(
            module_name='collections', attrib_name='namedtuple', asname='namedtuple'
        )
        from1str = (
            "FromImport(module_name='collections', "
            "attrib_name='namedtuple', "
            "asname='namedtuple')"
        )

        assert repr(from1) == from1str

    def test_import_repr_multifrom(self):
        mf1 = MultiFromImport(
            module_name='collections', attrib_names=['namedtuple', 'defaultdict']
        )
        mf1str = (
            "MultiFromImport(module_name='collections', "
            "attrib_names=['namedtuple', 'defaultdict'])"
        )
        assert repr(mf1) == mf1str

    def test_import_repr_tryexcept(self):
        te1 = TryExceptImport(
            module_name='tomllib', except_module='tomli', asname='tomllib'
        )
        te1str = (
            "TryExceptImport("
            "module_name='tomllib', "
            "except_module='tomli', "
            "asname='tomllib')"
        )

        assert repr(te1) == te1str

    def test_import_repr_tryexceptfrom(self):
        tef1 = TryExceptFromImport("tomllib", "loads", "tomli", "loads", "loads")

        tef1str = (
            "TryExceptFromImport("
            "module_name='tomllib', "
            "attribute_name='loads', "
            "except_module='tomli', "
            "except_attribute='loads', "
            "asname='loads')"
        )

        assert repr(tef1) == tef1str

    def test_import_repr_tryfallback(self):
        tf = TryFallbackImport("tomllib", None)

        tfstr = "TryFallbackImport(module_name='tomllib', fallback=None, asname='tomllib')"

        assert repr(tf) == tfstr

    def test_importer_repr(self):
        globs = globals()
        imports = [ModuleImport("functools"), FromImport("collections", "namedtuple")]
        laz = LazyImporter(imports=imports, globs=globs)

        laz_str = f"LazyImporter(imports={imports!r}, globs={globs!r})"

        assert repr(laz) == laz_str


class TestGatherImports:

    def test_asname_gather(self):
        importer = LazyImporter(
            [
                ModuleImport("collections.abc", "abc"),
            ]
        )

        assert dir(importer) == ["abc"]
        assert importer._importers == {"abc": ModuleImport("collections.abc", "abc")}

    def test_from_gather(self):
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

    def test_mixed_gather(self):
        importer = LazyImporter(
            [
                ModuleImport("collections"),
                ModuleImport("functools", "ft"),
                FromImport("dataclasses", "dataclass"),
                FromImport("typing", "NamedTuple", "nt"),
            ]
        )

        assert dir(importer) == ["collections", "dataclass", "ft", "nt"]

        assert importer._importers == {
            "collections": ModuleImport("collections", asname="collections"),
            "dataclass": FromImport("dataclasses", "dataclass"),
            "ft": ModuleImport("functools", "ft"),
            "nt": FromImport("typing", "NamedTuple", "nt"),
        }

    def test_multi_from(self):
        multi_from = MultiFromImport(
            "collections", ["defaultdict", ("namedtuple", "nt"), "OrderedDict"]
        )
        from_imp = FromImport("functools", "partial")
        mod_imp = ModuleImport("importlib.util", asname="importlib_util")

        importer = LazyImporter([multi_from, from_imp, mod_imp])

        assert dir(importer) == sorted(
            ["defaultdict", "nt", "OrderedDict", "partial", "importlib_util"]
        )

        assert importer._importers == {
            "defaultdict": multi_from,
            "nt": multi_from,
            "OrderedDict": multi_from,
            "partial": from_imp,
            "importlib_util": mod_imp,
        }


class TestLevels:
    def test_relative_fromimport_basename(self):
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

    def test_relative_exceptimport_basename(self):
        tryexcept_imp_level = TryExceptImport(
            "..submodreal", "...submodexcept", "asname"
        )

        assert tryexcept_imp_level.import_level == 2
        assert tryexcept_imp_level.except_import_level == 3


def test_import_grouper_access():
    """
    Test that the ImporterGrouper has been placed on the class
    """
    assert isinstance(LazyImporter._importers, _ImporterGrouper)


def test_no_globs_without_getframe():
    with patch("sys._getframe") as getframe_mock:
        getframe_mock.side_effect = AttributeError("_getframe missing")

        importer = LazyImporter()

    assert importer._globals is None

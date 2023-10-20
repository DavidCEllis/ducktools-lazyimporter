import sys

import pytest

from ducktools.lazyimporter import (
    LazyImporter,
    ModuleImport,
    FromImport,
    MultiFromImport
)


def test_imports_lazy():
    laz = LazyImporter([
        ModuleImport("example_1"),
        FromImport("example_2", "item", asname="i"),
    ])

    assert "example_1" not in sys.modules
    assert "example_2" not in sys.modules
    laz.example_1
    assert "example_1" in sys.modules
    assert "example_2" not in sys.modules
    laz.i
    assert "example_2" in sys.modules

    assert laz.i == "example"

    # Check the imports are the correct objects
    import example_1  # noqa
    import example_2  # noqa

    assert example_1 is laz.example_1
    assert example_2.item is laz.i


def test_imports_submod():
    laz_nosub = LazyImporter([
        ModuleImport("ex_mod")
    ])

    laz_sub = LazyImporter([
        ModuleImport("ex_mod.ex_submod")
    ])

    # Import ex_mod
    assert laz_nosub.ex_mod.name == "ex_mod"

    with pytest.raises(AttributeError):
        laz_nosub.ex_mod.ex_submod

    assert laz_sub.ex_mod.name == "ex_mod"
    assert laz_sub.ex_mod.ex_submod.name == "ex_submod"


def test_submod_from():
    laz = LazyImporter([
        FromImport("ex_mod.ex_submod", "name"),
    ])

    assert laz.name == "ex_submod"


def test_submod_multifrom():
    laz = LazyImporter([
        MultiFromImport("ex_mod.ex_submod", ["name", ("name2", "othername")]),
    ])

    assert laz.name == "ex_submod"
    assert laz.othername == "ex_submod2"


def test_relative_import():
    import example_modules.lazy_submod_ex as lse

    laz = lse.lazy_submod_from_import()
    assert laz.name == "ex_submod"

    laz = lse.lazy_submod_multi_from_import()
    assert laz.name == "ex_submod"
    assert laz.othername == "ex_submod2"


def test_submod_relative_import():
    from example_modules.ex_othermod import laz

    assert laz.name == "ex_submod"

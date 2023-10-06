import sys

import pytest

from lazy_importer import lazy_importer, ModuleImport, FromImport


def test_imports_lazy():
    laz = lazy_importer([
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


def test_imports_submod():
    laz_nosub = lazy_importer([
        ModuleImport("ex_mod")
    ])

    laz_sub = lazy_importer([
        ModuleImport("ex_mod.ex_submod")
    ])

    # Import ex_mod
    assert laz_nosub.ex_mod.name == "ex_mod"

    with pytest.raises(AttributeError):
        laz_nosub.ex_mod.ex_submod

    assert laz_sub.ex_mod.name == "ex_mod"
    assert laz_sub.ex_mod.ex_submod.name == "ex_submod"

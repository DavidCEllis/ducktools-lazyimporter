from lazy_importer import ModuleImport, FromImport, LazyImporterMaker


def test_equal_module():
    mod1 = ModuleImport("collections")
    mod2 = ModuleImport("collections")

    assert mod1 == mod2

    mod2 = ModuleImport("collections", "c")

    assert mod1 != mod2


def test_no_duplication():
    importer_maker = LazyImporterMaker([
        ModuleImport("collections"),
        ModuleImport("collections")
    ])

    plain, _, _ = importer_maker._sort_imports()

    assert plain == {"collections": {"collections"}}


def test_submodule_gather():
    importer_maker = LazyImporterMaker([
        ModuleImport("collections.abc"),
    ])

    plain, _, _ = importer_maker._sort_imports()

    assert plain == {
        "collections": {"collections", "collections.abc"}
    }


def test_asname_gather():
    importer_maker = LazyImporterMaker([
        ModuleImport("collections.abc", "abc"),
    ])

    _, asname, _ = importer_maker._sort_imports()

    assert asname == [ModuleImport("collections.abc", "abc")]


def test_from_gather():
    importer_maker = LazyImporterMaker([
        FromImport("dataclasses", "dataclass"),
        FromImport("dataclasses", "dataclass", "dc")
    ])

    _, _, from_imports = importer_maker._sort_imports()

    assert from_imports == [
        FromImport("dataclasses", "dataclass"),
        FromImport("dataclasses", "dataclass", "dc")
    ]


def test_mixed_gather():
    importer_maker = LazyImporterMaker([
        ModuleImport("collections"),
        ModuleImport("collections.abc"),
        ModuleImport("functools", "ft"),
        FromImport("dataclasses", "dataclass"),
        FromImport("typing", "NamedTuple", "nt"),
    ])

    plain, asname, from_ = importer_maker._sort_imports()

    assert plain == {
        "collections": {"collections", "collections.abc"}
    }

    assert asname == [ModuleImport("functools", "ft")]

    assert from_ == [
        FromImport("dataclasses", "dataclass"),
        FromImport("typing", "NamedTuple", "nt")
    ]


def test_dir():
    importer_maker = LazyImporterMaker([
        ModuleImport("collections"),
        ModuleImport("collections.abc"),
        ModuleImport("functools", "ft"),
        FromImport("dataclasses", "dataclass"),
        FromImport("typing", "NamedTuple", "nt"),
    ])

    laz = importer_maker.get_lazy_importer_object()

    assert sorted(dir(laz)) == sorted(
        ["collections", "ft", "dataclass", "nt"]
    )
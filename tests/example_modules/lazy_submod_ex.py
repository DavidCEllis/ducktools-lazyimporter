from ducktools.lazyimporter import (
    LazyImporter,
    FromImport,
    MultiFromImport,
)


def lazy_submod_from_import():
    laz = LazyImporter(
        [FromImport(".ex_mod.ex_submod", "name")],
        globs=globals(),
    )

    return laz


def lazy_submod_multi_from_import():
    laz = LazyImporter(
        [MultiFromImport(".ex_mod.ex_submod", ["name", ("name2", "othername")])],
        globs=globals(),
    )

    return laz

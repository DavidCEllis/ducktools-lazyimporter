from ducktools.lazyimporter import (
    LazyImporter,
    FromImport,
)

name = "ex_othermod"

laz = LazyImporter(
    [FromImport("..ex_mod.ex_submod", "name")],
    globs=globals(),
)

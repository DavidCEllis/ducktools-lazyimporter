from lazy_importer import LazyImporter, FromImport

laz = LazyImporter(
    [FromImport("..ex_mod.ex_submod", "name")],
    globs=globals(),
)

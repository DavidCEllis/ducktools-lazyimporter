from ducktools.lazyimporter import (
    LazyImporter,
    FromImport,
    get_module_funcs,
)

name = "ex_othermod"

laz = LazyImporter(
    [FromImport("..ex_mod.ex_submod", "name", "submod_name")],
    globs=globals(),
)

__getattr__, __dir__ = get_module_funcs(laz, module_name=__name__)

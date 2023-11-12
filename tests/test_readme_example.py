# README EXAMPLE CODE #

# NOTE: This is a simplified example using importlib.import_module
import importlib
from ducktools.lazyimporter import ImportBase, LazyImporter


class IfElseImporter(ImportBase):
    def __init__(self, condition, module_name, else_module_name, asname):
        self.condition = condition
        self.module_name = module_name
        self.else_module_name = else_module_name
        self.asname = asname

        if not self.asname.isidentifier():
            raise ValueError(f"{self.asname} is not a valid python identifier.")

    def do_import(self, globs=None):
        if globs is not None:
            package = globs.get('__name__')
        else:
            package = None

        if self.condition:
            mod = importlib.import_module(self.module_name, package)
        else:
            mod = importlib.import_module(self.else_module_name, package)

        return {self.asname: mod}


# Test for readme example code
def test_ifelse_importer():
    laz_if = LazyImporter([
        IfElseImporter(
            condition=True,
            module_name="ex_mod",
            else_module_name="ex_othermod",
            asname="ex_mod"
        )
    ])

    laz_else = LazyImporter([
        IfElseImporter(
            condition=False,
            module_name="ex_mod",
            else_module_name="ex_othermod",
            asname="ex_mod"
        )
    ])

    assert laz_if.ex_mod.name == "ex_mod"
    assert laz_else.ex_mod.name == "ex_othermod"

# README EXAMPLE CODE #

# NOTE: This is a simplified example using importlib.import_module
import importlib
from ducktools.lazyimporter import ImportBase, LazyImporter, FromImport


class IfElseImporter(ImportBase):
    def __init__(self, condition, module_name, else_module_name, asname):
        self.condition = condition
        self.module_name = module_name
        self.else_module_name = else_module_name
        self.asname = asname

        if not self.asname.isidentifier():  # pragma: no cover
            raise ValueError(f"{self.asname} is not a valid python identifier.")

    def import_objects(self, globs=None):
        if globs is not None:
            package = globs.get('__name__')
        else:  # pragma: no cover
            package = None

        if self.condition:
            mod = importlib.import_module(self.module_name, package)
        else:
            mod = importlib.import_module(self.else_module_name, package)

        return {self.asname: mod}


# Test for readme example code
def test_ifelse_importer():
    laz_if = LazyImporter(
        [
            IfElseImporter(
                condition=True,
                module_name="ex_mod",
                else_module_name="ex_othermod",
                asname="ex_mod",
            )
        ]
    )

    laz_else = LazyImporter(
        [
            IfElseImporter(
                condition=False,
                module_name="ex_mod",
                else_module_name="ex_othermod",
                asname="ex_mod",
            )
        ]
    )

    assert laz_if.ex_mod.name == "ex_mod"
    assert laz_else.ex_mod.name == "ex_othermod"


def test_doc_example():
    from dataclasses import dataclass

    laz = LazyImporter(
        [
            FromImport("dataclasses", "fields"),
            FromImport("json", "dumps"),
        ]
    )

    def _dataclass_default(dc):
        # In general is_dataclass should be used, but for this case
        # in order to demonstrate laziness it is not.
        if hasattr(dc, "__dataclass_fields__"):
            fields = laz.fields(dc)
            return {f.name: getattr(dc, f.name) for f in fields}
        raise TypeError("Object is not a Dataclass")

    def dumps(obj, **kwargs):
        default = kwargs.pop("default", None)
        if default:

            def new_default(o):
                try:
                    return default(o)
                except TypeError:
                    return _dataclass_default(o)

        else:
            new_default = _dataclass_default
        kwargs["default"] = new_default

        return laz.dumps(obj, **kwargs)

    @dataclass
    class TestEx:
        answer: int
        question: str

    in_dict = {
        "answer": 42,
        "question": "What do you get if you multiply 6 by 9?",
    }

    ex = TestEx(**in_dict)
    output = laz.dumps(in_dict)

    assert dumps(ex) == output

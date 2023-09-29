"""
Rewrite a python file to use lazy imports.
"""
import itertools
import libcst as cst
import libcst.matchers as matchers
from libcst.helpers import get_full_name_for_node_or_raise as get_node_fullname

from prefab_classes import prefab

CTXMAN_NAME = "lazy_importer"
IMPORT_DICT_NAME = "_LAZY_IMPORTS"


def getattr_func(
    import_dict: str, module_tree: cst.Module, *, func_name="__getattr__"
) -> tuple[cst.CSTNode]:
    """
    Generate the CST for the getattr function to handle lazy loading

    :param module_tree: CST module object to use as config
    :param func_name: name of the getattr function - could be necessary if
                      a getattr function is already defined.
    :return: CST getattr function to be inserted into the new module body
    """

    source = (
        f"""
{import_dict}

def {func_name}(name):
    \"\"\"
    Lazy importer __getattr__ function
    
    Imports lazy attributes and assigns them to the module for future access.
    \"\"\"

    import sys
    
    try:
        lazy_import = {IMPORT_DICT_NAME}[name]

        this_module = sys.modules[__name__]

        import importlib

        match lazy_import:
            case (module_name, alias):
                module = importlib.import_module(module_name)
                setattr(this_module, alias, module)
                return module
            case (module_name, from_name, alias):
                module = importlib.import_module(module_name)
                obj = getattr(module, from_name)
                setattr(this_module, alias, obj)
                return obj
            case _:
                raise TypeError(f"Received unrecognised object {{lazy_import}}")

    except (KeyError, AttributeError):
        raise AttributeError(
            f"Module {{__name__}} has no attribute {{name!r}}."
        )          
    """
    ).strip()

    cst_obj = cst.parse_module(source, config=module_tree.config_for_parsing).body
    return cst_obj


def _is_lazy_importer_block(item: cst.CSTNode):
    return (
        isinstance(item, cst.With)
        and len(item.items) == 1
        and isinstance(item.items[0].item, cst.Call)
        and item.items[0].item.func.value == CTXMAN_NAME
    )


@prefab
class LazyImports:
    module_imports: list[tuple[str, str]]
    from_imports: list[tuple[str, str, str]]
    original_containers: list[cst.With]

    @property
    def import_dict(self) -> str:
        """
        Generate the lookup dictionary for __getattr__

        :return: import dict str to be added to the template.
        """
        import_chain = itertools.chain(self.module_imports, self.from_imports)

        key_pairs = ", \n    ".join(f"{item[-1]!r}: {item!r}" for item in import_chain)

        import_dict = f"{IMPORT_DICT_NAME} = {{\n    {key_pairs}\n}}"

        return import_dict

    @classmethod
    def from_tree(cls, tree: cst.Module):
        lazy_containers = [item for item in tree.body if _is_lazy_importer_block(item)]

        visitor = GatherImports()

        for container in lazy_containers:
            container.visit(visitor)

        return LazyImports(
            visitor.module_imports, visitor.from_imports, lazy_containers
        )


class GatherImports(cst.CSTVisitor):
    def __init__(self):
        self.module_imports = []
        self.from_imports = []

    def visit_Import(self, node: cst.Import):
        for alias in node.names:
            base_name = get_node_fullname(alias.name)

            if isinstance(alias.name, cst.Attribute) and alias.asname is None:
                raise ValueError(
                    f"Submodules can only be lazily imported "
                    f"using a valid identifier as an alias. "
                    f"For example, `import {base_name} as foo`."
                )

            if alias.asname is not None:
                asname = alias.asname.name.value
            else:
                asname = base_name

            self.module_imports.append((base_name, asname))

    def visit_ImportFrom(self, node: cst.ImportFrom):
        module_name = get_node_fullname(node.module)

        for attrib in node.names:
            attrib_name = attrib.name.value
            if attrib_name == "*":
                raise ValueError("'*' imports are not supported by the lazy importer")

            if attrib.asname is None:
                asname = attrib_name
            else:
                asname = attrib.asname.name.value

            self.from_imports.append((module_name, attrib_name, asname))


class CleanupLazyImporters(cst.CSTTransformer):
    """
    Remove remaining 'with lazy_importer()' calls and 'from lazy_importer import lazy_importer' statement.
    """

    def leave_ImportFrom(
        self, original_node: cst.ImportFrom, updated_node: cst.ImportFrom
    ):
        """
        Remove the from lazy_importer import lazy_importer statement.
        """
        if (
            original_node.module.value == CTXMAN_NAME
            and original_node.names[0].name.value == CTXMAN_NAME
        ):
            return cst.RemoveFromParent()

        return original_node

    def leave_With(self, original_node: cst.With, updated_node: cst.With):
        """
        Remove any remaining 'with lazy_importer()' calls that have been placed inside other blocks.
        Technically these are invalid but just convert them to regular imports and collapse the block.
        """
        lazy_withitem = matchers.WithItem(matchers.Call(matchers.Name("lazy_importer")))

        withitems = list(original_node.items)

        for i, withitem in enumerate(original_node.items):
            if matchers.matches(withitem, lazy_withitem):
                if len(original_node.items) > 1:
                    # I am making the assumption that nobody's using lazy_importer()
                    # twice in 1 with block
                    new_items = withitems[:i] + withitems[i + 1 :]
                    return updated_node.with_changes(items=new_items)
                else:
                    return cst.FlattenSentinel(updated_node.body.body)

        return updated_node


def make_imports_lazy(src: str) -> str:
    """
    Take python source code with lazy imports and replace them with the __getattr__
    lazy import implementation.

    :param src: python source code with lazy_import blocks.
    :return: source code with lazy imports implemented.
    """
    module = cst.parse_module(src)
    imps = LazyImports.from_tree(module)

    lazy_mechanism = getattr_func(
        import_dict=imps.import_dict,
        module_tree=module,
    )

    new_body = []
    block_inserted = False  # Has the lazy importer block been inserted yet
    for item in module.body:
        if _is_lazy_importer_block(item):
            if not block_inserted:
                new_body.extend(lazy_mechanism)
                block_inserted = True
        else:
            new_body.append(item)

    new_module = module.with_changes(body=new_body)

    new_module = new_module.visit(CleanupLazyImporters())

    return new_module.code

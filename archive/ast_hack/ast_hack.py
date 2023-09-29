"""
Hack the AST to convert regular imports into delayed imports.
"""
import os

from . import _ast_vendor as ast
from . import CTXMAN_NAME


IMPORT_DICT_NAME = "_LAZY_IMPORTS"


def getattr_func():
    source = (f"""
import sys

def __getattr__(name):
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
                raise TypeError("Received impossible object")

    except (KeyError, AttributeError):
        raise AttributeError(
            f"Module {{__name__}} has no attribute {{name!r}}."
        )          
    """).strip()

    ast_obj = ast.parse(source).body
    return ast_obj


class LazyImports:
    module_imports: list[ast.Import]
    from_imports: list[ast.ImportFrom]
    original_containers: list[ast.With]

    def __init__(self, module_imports, from_imports, original_containers):
        self.module_imports = module_imports
        self.from_imports = from_imports
        self.original_containers = original_containers

    def __str__(self):
        module_texts = ", ".join(ast.dump(item) for item in self.module_imports)
        from_texts = ", ".join(ast.dump(item) for item in self.from_imports)

        return (
            f"{self.__class__.__name__}("
            f"module_imports=[{module_texts}], "
            f"from_imports=[{from_texts}])"
        )

    @property
    def _import_dict(self):
        mod_dict = {}
        for imp in self.module_imports:
            for name in imp.names:
                if name.asname:
                    mod_dict[name.asname] = (name.name, name.asname)
                else:
                    mod_dict[name.name] = (name.name, name.name)

        for imp in self.from_imports:
            for name in imp.names:
                if name.asname:
                    mod_dict[name.asname] = (imp.module, name.name, name.asname)
                else:
                    mod_dict[name.name] = (imp.module, name.name, name.name)

        return mod_dict

    @property
    def import_dict_assignment(self):
        """
        Generate the lookup dictionary for __getattr__
        :return:
        """
        key_pairs = ", ".join(f"{k!r}: {v!r}" for k, v in self._import_dict.items())

        template = (
            f"{IMPORT_DICT_NAME} = {{ {key_pairs} }}"
        )

        import_dict = ast.parse(template).body[0]

        return import_dict

    @classmethod
    def from_tree(cls, tree: ast.Module):
        lazy_containers = [
            item for item in tree.body
            if isinstance(item, ast.With)
               and len(item.items) == 1
               and isinstance(item.items[0].context_expr, ast.Call)
               and item.items[0].context_expr.func.id == CTXMAN_NAME
        ]

        module_imports = []
        from_imports = []

        for container in lazy_containers:
            for imp in container.body:
                if isinstance(imp, ast.Import):
                    for item in imp.names:
                        if "." in item.name and not item.asname:
                            raise ValueError(
                                f"Submodules can only be lazily imported "
                                f"using a valid identifier as an alias. "
                                f"For example, `import {item.name} as foo`."
                            )

                    module_imports.append(imp)
                elif isinstance(imp, ast.ImportFrom):
                    if imp.names[0].name == "*":
                        raise ValueError(
                            "'*' imports are not supported by the lazy importer"
                        )
                    from_imports.append(imp)
                else:
                    raise TypeError(
                        f"Contents of {CTXMAN_NAME} context block "
                        f"MUST only be import statements."
                    )

        return LazyImports(module_imports, from_imports, lazy_containers)


def hack_ast(src: str) -> ast.tree:
    """
    Parse the source code string into an AST and replace imports within a lazy_import block
    with delayed imports using module level `__getattr__`.

    :param src: Source code as string.
    :return: AST tree with lazy imports in place.
    """
    tree = ast.parse(src)

    containers = LazyImports.from_tree(tree)

    base_funcs = getattr_func()

    new_insert = [*base_funcs, containers.import_dict_assignment]

    for lazy_block in containers.original_containers:
        tree.body.remove(lazy_block)

    tree.body = new_insert + tree.body

    ast.fix_missing_locations(tree)

    return tree


def rewrite_source(src_path: str | os.pathlike, dest_path: str | os.pathlike):
    """
    Rewrite source code to use lazy imports using 

    :param src_path: _description_
    :param dest_path: _description_
    :raises ValueError: _description_
    """
    if src_path == dest_path:
        raise ValueError("Source must be different to destination.")

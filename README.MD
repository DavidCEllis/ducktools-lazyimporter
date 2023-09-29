# Lazy importer #

Convert `lazy_importer` blocks into lazy imports that use module `__getattr__`.

Intended to allow library developers to delay imports to slower modules or submodules
while allowing users to import them from 'nicer' places if needed.

## How to use ##

Write a block with a `lazy_importer`:

example.py
```python
from lazy_importer import lazy_importer

with lazy_importer():
    import this_module.slow_submodule1 as slow_submodule1
    
    from .slow_submodule2 import useful_function1

    from .slow_submodule3 import other_func as useful_function2

__all__ = ["useful_function1", "useful_function2"]
```

run in terminal:
```
python -m lazy_importer example.py example_output.py
```

example_output.py
```python
_LAZY_IMPORTS = {
    'slow_submodule1': ('this_module.slow_submodule1', 'slow_submodule1'), 
    'useful_function1': ('.slow_submodule2', 'useful_function1', 'useful_function1'), 
    'useful_function2': ('.slow_submodule3', 'other_func', 'useful_function2')
}

def __getattr__(name):
    """
    Lazy importer __getattr__ function
    
    Imports lazy attributes and assigns them to the module for future access.
    """

    import sys
    
    try:
        lazy_import = _LAZY_IMPORTS[name]

        this_module = sys.modules[__name__]

        import importlib

        match lazy_import:
            case (module_name, alias):
                module = importlib.import_module(module_name)
                setattr(this_module, alias, module)
                return module
            case (module_name, from_name, alias):
                module = importlib.import_module(module_name, package=__name__)
                obj = getattr(module, from_name)
                setattr(this_module, alias, obj)
                return obj
            case _:
                raise TypeError(f"Received unrecognised object {lazy_import}")

    except (KeyError, AttributeError):
        raise AttributeError(
            f"Module {__name__} has no attribute {name!r}."
        )

__all__ = ["useful_function1", "useful_function2"]
```

## Additional Usage Notes ##

**`lazy_importer` must be used as a `with` import as shown without being renamed in order to 
work correctly. This is because the CST rewriting looks for the name itself and does
not attempt to track if it has been renamed.**

`lazy_importer` itself is a noop, without the conversion the imports will work as standard
eager imports.

`with lazy_importer:` blocks will only be converted at the top level of a module. If used
within another block the with statement will be removed and imports converted to regular
eager imports.

If you wish to use the lazy imports created from within certain parts of the module you will need
to access the module object to trigger the access via `__getattr__`.
Usually via `this_module = sys.modules[__name__]` or something similar.


## How it works ##

`libcst` is used to convert the module into a CST which is then modified to place the 
`__getattr__` function and remove the `with lazy_import():` blocks.
Note that **anything** contained within the block will be removed with the block.
# lazy_importer.py #

Create an object to handle lazily importing from other modules.

## Use Case ##

There are two main use cases this is designed for.

### Replacing in-line imports used in a module ###

Sometimes it is useful to use tools from a module that has a significant import time.
If this is part of a function/method that won't necessarily always be used it is 
common to delay the import and place it inside the function/method.

Regular import within function:
```python
def get_copy(obj):
    from copy import deepcopy
    return deepcopy(obj)
```

With a LazyImporter:
```python
from lazy_importer import LazyImporter, FromImport

laz = LazyImporter([FromImport("copy", "deepcopy")])

def get_copy(obj):
    return laz.deepcopy(obj)
```

While the LazyImporter is more verbose, it only invokes the import mechanism
once when first accessed, while placing the import within the function invokes
it every time the function is called. This can be a significant overhead if
the function ends up used in a loop.

This also means that if the attribute is accessed anywhere it will be imported
and in place wherever it is used.

### Delaying the import of parts of a module's public API ###

Eager import:
```python
from .submodule import useful_tool

__all__ = [..., "useful_tool"]
```

Lazy import:
```python
from lazy_importer import LazyImporter, FromImport, get_module_funcs

__all__ = [..., "useful_tool"]

laz = LazyImporter([FromImport("parent_module.submodule", "useful_tool")])
__getattr__, __dir__ = get_module_funcs(laz, __name__)
```

## How to use ##

```python
from lazy_importer import (
    LazyImporter,
    ModuleImport,
    FromImport,
    MultiFromImport,
    get_importer_state,
)

# Setup attributes but don't perform any imports
laz = LazyImporter([
    MultiFromImport(
        "collections", [("namedtuple", "nt"), "OrderedDict"]
    ),
    FromImport("pprint", "pprint"),
    FromImport("functools", "partial"),
    ModuleImport("inspect"),
])

print("Possible attributes:")
laz.pprint(dir(laz))
print()

print("pprint imported:")
laz.pprint(get_importer_state(laz))
print()

_ = laz.nt
print("Collections elements imported:")
laz.pprint(get_importer_state(laz))
print()

_ = laz.partial
print("Functools elements imported:")
laz.pprint(get_importer_state(laz))
print()
```

Output:
```
Possible attributes:
['OrderedDict', 'inspect', 'nt', 'partial', 'pprint']

pprint imported:
{'imported_attributes': {'pprint': <function pprint at ...>},
 'lazy_attributes': ['OrderedDict', 'inspect', 'nt', 'partial']}

Collections elements imported:
{'imported_attributes': {'OrderedDict': <class 'collections.OrderedDict'>,
                         'nt': <function namedtuple at ...>,
                         'pprint': <function pprint at ...>},
 'lazy_attributes': ['inspect', 'partial']}

Functools elements imported:
{'imported_attributes': {'OrderedDict': <class 'collections.OrderedDict'>,
                         'nt': <function namedtuple at ...>,
                         'partial': <class 'functools.partial'>,
                         'pprint': <function pprint at ...},
 'lazy_attributes': ['inspect']}
```
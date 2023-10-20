# ducktools: lazyimporter #

Create an object to handle lazily importing from other modules.

Nearly every form of "lazyimporter" module name is taken on PyPI so this is namespaced.

Intended to help save on start time where some modules are only needed for specific
functions while allowing information showing the import information to appear at
the top of a module where expected.

This form of import works by creating a specific LazyImporter object that lazily
imports modules or module attributes when the module or attribute is accessed
on the object.

## Example ##

Example using the packaging module.

```python
__version__ = "v0.1.5"

from ducktools.lazyimporter import LazyImporter, FromImport

laz = LazyImporter([
    FromImport("packaging.version", "Version")
])

def is_newer_version(version_no: str) -> bool:
    """Check if a version number given indicates 
    a newer version than this package."""
    this_ver = laz.Version(__version__) 
    new_ver = laz.Version(version_no)
    return new_ver > this_ver

# Import will only occur when the function is called and 
# laz.Version is accessed
print(is_newer_version("v0.2.0"))
```

## Hasn't this already been done ##

Yes.

But...

Most implementations rely on stdlib modules that are themselves slow to import
(for example: typing, importlib.util, logging).
By contrast `lazyimporter` only uses modules that python imports on launch
as part of `site`.

`lazyimporter` does not attempt to propagate laziness, only the modules provided
to `lazyimporter` directly will be imported lazily. Any subdependencies of those 
modules will be imported eagerly as if the import statement is placed where the 
importer attribute is first accessed. 

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
from ducktools.lazyimporter import LazyImporter, FromImport

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
from ducktools.lazyimporter import LazyImporter, FromImport, get_module_funcs

__all__ = [..., "useful_tool"]

laz = LazyImporter(
    [FromImport(".submodule", "useful_tool")],
    globs=globals(),  # If relative imports are used, globals() must be provided.
)
__getattr__, __dir__ = get_module_funcs(laz, __name__)
```

## Demonstration of when imports occur ##

```python
from ducktools.lazyimporter import (
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
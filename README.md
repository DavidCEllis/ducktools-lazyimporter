# ducktools: lazyimporter #

Create an object to handle lazily importing from other modules.

Nearly every form of "lazyimporter" module name is taken on PyPI so this is namespaced.

Intended to help save on start time where some modules are only needed for specific
functions while allowing information showing the import information to appear at
the top of a module where expected.

This form of import works by creating a specific LazyImporter object that lazily
imports modules or module attributes when the module or attribute is accessed
on the object.

## How to download ##

Download from PyPI:
    `python -m pip install ducktools-lazyimporter`

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
(for example: typing, importlib.util, logging, inspect, ast).
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

## The import classes ##

In all of these instances `modules` is intended as the first argument
to `LazyImporter` and all attributes would be accessed from the 
`LazyImporter` instance and not in the global namespace.

eg:
```python
from ducktools.lazyimporter import LazyImporter, ModuleImport

modules = [ModuleImport("functools")]
laz = LazyImporter(modules)
laz.functools  # provides access to the module "functools"
```

### ModuleImport ###

`ModuleImport` is used for your basic module style imports.

```python
from ducktools.lazyimporter import ModuleImport

modules = [
    ModuleImport("module"),
    ModuleImport("other_module", "other_name"),
    ModuleImport("base_module.submodule", asname="short_name"),
]
```

is equivalent to 

```
import module
import other_module as other_name
import base_module.submodule as short_name
```

when provided to a LazyImporter.

### FromImport and MultiFromImport ###

`FromImport` is used for standard 'from' imports, `MultiFromImport` for importing
multiple items from the same module. By using a `MultiFromImport`, when the first
attribute is accessed, all will be assigned on the LazyImporter.

```python
from ducktools.lazyimporter import FromImport, MultiFromImport

modules = [
    FromImport("dataclasses", "dataclass"),
    FromImport("functools", "partial", "partfunc"),
    MultiFromImport("collections", ["namedtuple", ("defaultdict", "dd")]),
]
```

is equivalent to

```python
from dataclasses import dataclass
from functools import partial as partfunc
from collections import namedtuple, defaultdict as dd
```

when provided to a LazyImporter.

### TryExceptImport ###

`TryExceptImport` is used for compatibility where a module may not be available
and so a fallback module providing the same functionality should be used. For
example when a newer version of python has a stdlib module that has replaced
a third party module that was used previously.

```python
from ducktools.lazyimporter import TryExceptImport

modules = [
    TryExceptImport("tomllib", "tomli", "tomllib"),
]
```

is equivalent to

```python
try:
    import tomllib as tomllib
except ImportError:
    import tomli as tomllib
```

when provided to a LazyImporter.

## How does it work ##

The following lazy importer:

```python
from ducktools.lazyimporter import LazyImporter, FromImport

laz = LazyImporter([FromImport("functools", "partial")])
```

Generates an object that's roughly equivalent to this:

```python
class SpecificLazyImporter:
    def __getattr__(self, name):
        if name == "partial":
            from functools import partial
            setattr(self, name, partial)
            return partial
        
        raise AttributeError(...)

laz = SpecificLazyImporter()
```

The first time the attribute is accessed the import is done and the output
is stored on the instance, so repeated access immediately gets the desired 
object and the import mechanism is only invoked once.

(The actual `__getattr__` function uses a dictionary lookup and delegates importing
to the FromImport class. Names are all dynamic and imports are done through
the `__import__` function.)

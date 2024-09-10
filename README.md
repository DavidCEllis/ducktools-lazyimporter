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

## Why use a lazy importer? ##

One obvious use case is if you are creating a simple CLI application that you wish to feel fast.
If the application has multiple pathways a lazy importer can improve performance by avoiding
loading the modules that are only needed for heavier pathways. (It may also be worth looking
at what library you are using for CLI argument parsing.)

I created this so I could use it on my own projects so here's an example of the performance
of `ducktools-env` with and without lazy imports.

With lazy imports:
```commandline
hyperfine -w3 -r20 "python -m ducktools.env run examples\inline\empty_312_env.py"
```
```
Benchmark 1: python -m ducktools.env run examples\inline\empty_312_env.py
  Time (mean ± σ):      87.1 ms ±   1.1 ms    [User: 52.2 ms, System: 22.4 ms]
  Range (min … max):    85.2 ms …  89.1 ms    20 runs
```

Without lazy imports (by setting `DUCKTOOLS_EAGER_IMPORT=true`):
```commandline
hyperfine -w3 -r20 "python -m ducktools.env run examples\inline\empty_312_env.py"
```
```
Benchmark 1: python -m ducktools.env run examples\inline\empty_312_env.py
  Time (mean ± σ):     144.2 ms ±   1.4 ms    [User: 84.8 ms, System: 45.3 ms]
  Range (min … max):   141.0 ms … 146.7 ms    20 runs
```

In this case the module is searching for a matching python environment to run the script in, 
the environment already exists and is cached so there is no need to load the code required 
for constructing new environments. This timer includes the time to relaunch the correct
python environment and run the (empty) script.

## Hasn't this already been done ##

Yes.

But...

Most implementations rely on stdlib modules that are themselves slow to import
(for example: typing, importlib.util, logging, inspect, ast).
By contrast `ducktools-lazyimporter` only uses modules that python imports on launch.

`ducktools-lazyimporter` does not attempt to propagate laziness, only the modules provided
to `ducktools-lazyimporter` directly will be imported lazily. Any subdependencies of those 
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

### TryExceptImport, TryExceptFromImport and TryFallbackImport ###

`TryExceptImport` is used for compatibility where a module may not be available
and so a fallback module providing the same functionality should be used. For
example when a newer version of python has a stdlib module that has replaced
a third party module that was used previously.

```python
from ducktools.lazyimporter import TryExceptImport, TryExceptFromImport, TryFallbackImport

modules = [
    TryExceptImport("tomllib", "tomli", "tomllib"),
    TryExceptFromImport("tomllib", "loads", "tomli", "loads", "loads"),
    TryFallbackImport("tomli", None),
]
```

is roughly equivalent to

```python
try:
    import tomllib as tomllib
except ImportError:
    import tomli as tomllib

try:
    from tomllib import loads as loads
except ImportError:
    from tomli import loads as loads

try:
    import tomli
except ImportError:
    tomli = None
```

when provided to a LazyImporter.

## Environment Variables ##

There are two environment variables that can be used to modify the behaviour for
debugging purposes.

If `DUCKTOOLS_EAGER_PROCESS` is set to any value other than 'False' (case insensitive)
the initial processing of imports will be done on instance creation.

Similarly if `DUCKTOOLS_EAGER_IMPORT` is set to any value other than 'False' all imports
will be performed eagerly on instance creation (this will also force processing on import).

If they are unset this is equivalent to being set to False.

If there is a lazy importer where it is known this will not work 
(for instance if it is managing a circular dependency issue)
these can be overridden for an importer by passing values to `eager_process` and/or 
`eager_import` arguments to the `LazyImporter` constructer as keyword arguments.

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

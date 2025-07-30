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
of getting the help menu for `ducktools-env` with and without lazy imports.

With lazy imports:
```commandline
hyperfine -w3 -r20 "python -m ducktools.env --help"
```
```
Benchmark 1: python -m ducktools.env --help
  Time (mean ± σ):      41.4 ms ±   1.0 ms    [User: 21.1 ms, System: 15.9 ms]
  Range (min … max):    40.0 ms …  44.1 ms    20 runs
```

Without lazy imports (by setting `DUCKTOOLS_EAGER_IMPORT=true`):
```commandline
hyperfine -w3 -r20 "python -m ducktools.env --help"
```
```
Benchmark 1: python -m ducktools.env --help
  Time (mean ± σ):     112.8 ms ±   2.6 ms    [User: 78.1 ms, System: 35.9 ms]
  Range (min … max):   109.2 ms … 117.8 ms    20 runs
```

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
    globs=globals(),  # globals() is used for relative imports, LazyImporter will attempt to infer it if not provided
)
__getattr__, __dir__ = get_module_funcs(laz, __name__)  # __name__ will also be inferred if not given
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

```python
import module
import other_module as other_name
import base_module.submodule as short_name
```

when provided to a LazyImporter and accessed as follows:

```python
from ducktools.lazyimporter import LazyImporter
laz = LazyImporter(modules)

laz.module  # module
laz.other_name  # other_module
laz.short_name  # base_module.submodule
```

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

when provided to a LazyImporter and accessed as follows:

```python
from ducktools.lazyimporter import LazyImporter
laz = LazyImporter(modules)

laz.dataclass  # dataclasses.dataclass
laz.partfunc  # functools.partial
laz.namedtuple  # collections.namedtuple
laz.dd  # collections.defaultdict
```

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

when provided to a LazyImporter and accessed as follows:

```python
from ducktools.lazyimporter import LazyImporter
laz = LazyImporter(modules)

laz.tomllib  # tomllib / tomli
laz.loads  # tomllib.loads / tomli.loads
laz.tomli  # tomli / None
```

## Experimental import statement capture ##

There is an **experimental** mode that can capture import statements within a context block.

This is currently in a separate 'capture' submodule but may be merged (or lazily imported itself) in the future.

```python
from ducktools.lazyimporter import LazyImporter, get_importer_state
from ducktools.lazyimporter.capture import capture_imports

laz = LazyImporter()

with capture_imports(laz, auto_export=True):
    # Inside this block, imports are captured and converted to lazy imports on laz
    import functools
    from collections import namedtuple as nt

print(get_importer_state(laz))

# Note that the captured imports are *not* available in the module namespace
try:
    functools
except NameError:
    print("functools is not here")
```

Imports are placed on the lazy importer object as with the explicit syntax. Unlike the regular
syntax, these imports are exported by default.

This works by replacing and restoring the builtin `__import__` function that is called by the
import statement while in the block.

### Context Manager Caveats ###

* This only supports Module imports and From imports
  * The actual statement executes immediately and returns a placeholder, so a try/except can't work.
* Imports triggered inside functions or classes while within the block will still occur eagerly
* Imports triggered in other modules while within the block will still occur eagerly
* The context manager must be used at the module level
  * It will error if you use it inside a class or function scope
* As with the `ModuleImport` class, submodule imports without an assigned name are not supported.
* If other modules are also replacing `__import__` **simultaneously** this will probably fail.
  * In a library you may not be able to guarantee this.
  * Hopefully this will be resolvable.

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

## Logging imports ##

If you are finding that a certain module is always being imported and wish to investigate
how the module is being imported, there is now an environment variable that can be set
to print the stack to stderr whenever an import is triggered.

Set `DUCKTOOLS_REPORT_IMPORTS=true` in your environment and you will see `Import triggered:`
followed by the stack trace whenever a lazy importer first imports a module.

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

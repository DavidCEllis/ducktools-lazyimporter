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

when provided to a LazyImporter and accessed as follows:

```python
from ducktools.lazyimporter import LazyImporter
laz = LazyImporter(modules)

laz.tomllib  # tomllib / tomli
laz.loads  # tomllib.loads / tomli.loads
laz.tomli  # tomli / None
```

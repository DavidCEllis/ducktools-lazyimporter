# Welcome to Ducktools: Lazy Importer #

```{toctree}
---
maxdepth: 2
caption: "Contents:"
hidden: true
---
import_classes
capture_imports
examples
importer_state
extending
api
```

Ducktools: Lazy Importer is a module intended to make it easier to defer
imports until needed without requiring the import statement to be written
in-line.

The goal of deferring imports is to avoid importing modules that are not guaranteed
to be used in the course of running an application.

This can be done both on the side of the application, in deferring imports
only used in specific code paths and from the side of a library, providing
a nice API with easy access to modules without needing to import the module
in the case it is not used.

## Usage ##

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

## Indices and tables ##
* {ref}`genindex`
* {ref}`modindex`
* {ref}`search`
# Welcome to Ducktools: Lazy Importer #

```{toctree}
---
maxdepth: 2
caption: "Contents:"
hidden: true
---
examples
api
```

Ducktools: Lazy Importer is a module intended to make it easier to defer
imports until needed without requiring the import statement to be written
in-line.

The goal of deferring imports is to avoid importing modules that is not guaranteed
to be used in the course of running an application.
This can be done both on the side of the application, in deferring imports
only used in specific code paths and from the side of a library, providing
a nice API with easy access to modules without needing to import the module
in the case it is not used.

Importing an external module to use in a specific part of a function

```python
from ducktools.lazyimporter import LazyImporter, FromImport

laz = LazyImporter([FromImport("inspect", "getsource")])

def work_with_source(obj):
    src = laz.getsource(obj)  # import occurs only when this line first runs
    ...
```

Providing access to submodule attributes in the main module without importing
unless they are requested.

```python
from ducktools.lazyimporter import LazyImporter, FromImport, get_module_funcs

laz = LazyImporter(
    [FromImport(".funcs", "to_json")],
    globs=globals()  # Need to provide globals for relative imports
)

__getattr__, __dir__ = get_module_funcs(laz, __name__)
```


## Indices and tables ##
* {ref}`genindex`
* {ref}`modindex`
* {ref}`search`
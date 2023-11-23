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

There are two main use cases it is designed for:

Importing an external module to use in a specific part of a function

```python
from ducktools.lazyimporter import LazyImporter, FromImport

laz = LazyImporter([FromImport("inspect", "getsource")])

def work_with_source(obj):
    src = laz.getsource(obj)
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
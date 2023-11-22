# Welcome to Ducktools: Lazy Importer #

```{toctree}
---
maxdepth: 2
caption: "Contents:"
hidden: true
---
```

Ducktools: Lazy Importer is a module intended to make it easier to defer
imports until needed without requiring the import statement to be written
in-line.

Example (a json dump function for dataclasses):

```python
from ducktools.lazyimporter import LazyImporter, FromImport
laz = LazyImporter([
    FromImport("dataclasses", "fields"),
    FromImport("json", "dumps"),
])

def _dataclass_default(dc):
    # In general is_dataclass should be used, but for this case
    # in order to demonstrate laziness it is not.
    if hasattr(dc, "__dataclass_fields__"):
        fields = laz.fields(dc)
        return {f.name: getattr(dc, f.name) for f in fields}
    raise TypeError("Object is not a Dataclass")

def dumps(obj, **kwargs):
    default = kwargs.pop("default", None)
    if default:
        def new_default(o):
            try:
                return default(o)
            except TypeError:
                return _dataclass_default(o)
    else:
        new_default = _dataclass_default
    kwargs["default"] = new_default
    
    return laz.json.dumps(obj, **kwargs)
```


## Indices and tables ##
* {ref}`genindex`
* {ref}`modindex`
* {ref}`search`
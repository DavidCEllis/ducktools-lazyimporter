# Examples #

## A JSON dumps function with dataclass support ##

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
    
    return laz.dumps(obj, **kwargs)
```

